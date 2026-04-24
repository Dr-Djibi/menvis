import os
import sounddevice as sd
import soundfile as sf
import numpy as np
from openai import OpenAI
from config import Config

# ─── Initialisation du client Groq pour la voix (si possible) ───
def _get_groq_client():
    if Config.GROQ_API_KEY:
        return OpenAI(base_url=Config.GROQ_BASE_URL, api_key=Config.GROQ_API_KEY)
    return None

# ─── Classe pour l'enregistrement manuel (Start/Stop) ───
class ManualRecorder:
    def __init__(self, filename="temp_user_voice.wav", samplerate=16000):
        self.filename = filename
        self.samplerate = samplerate
        self.recording = False
        self.audio_data = []
        self.stream = None

    def start(self):
        print(f"[REC] Démarrage de l'enregistrement...")
        self.recording = True
        self.audio_data = []
        try:
            self.stream = sd.InputStream(
                samplerate=self.samplerate, 
                channels=1, 
                dtype='float32',
                callback=self._callback
            )
            self.stream.start()
            return True
        except Exception as e:
            print(f"[!] Erreur micro : {e}")
            self.recording = False
            return False

    def _callback(self, indata, frames, time, status):
        if self.recording:
            self.audio_data.append(indata.copy())

    def stop(self):
        print(f"[REC] Arrêt...")
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        if not self.audio_data:
            return None
            
        data = np.concatenate(self.audio_data, axis=0)
        sf.write(self.filename, data, self.samplerate)
        return self.filename

def transcribe_file(filename: str) -> str:
    """Transcrit l'audio. Priorité à Groq (Cloud/Rapide) sinon Whisper (Local)."""
    if not os.path.exists(filename):
        return ""
        
    # 1. Tentative via Groq (Zéro ressource locale, Ultra-rapide)
    client = _get_groq_client()
    if client:
        try:
            print("[Voice] Transcription via Groq (Cloud)...")
            with open(filename, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    file=(filename, audio_file.read()),
                    model="whisper-large-v3-turbo",
                    language="fr",
                    response_format="text"
                )
            if os.path.exists(filename): os.remove(filename)
            print(f"[Voice] Groq dit : {transcription}")
            return str(transcription).strip()
        except Exception as e:
            print(f"[Voice] Échec Groq : {e}. Basculement sur local...")

    # 2. Fallback Local (utilise CPU/RAM)
    try:
        from faster_whisper import WhisperModel
        print("[Voice] Transcription locale (Tiny)...")
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(filename, beam_size=5, language="fr", vad_filter=True)
        transcription = " ".join([segment.text for segment in segments]).strip()
        if os.path.exists(filename): os.remove(filename)
        return transcription
    except Exception as e:
        print(f"[Voice] Erreur local : {e}")
        if os.path.exists(filename): os.remove(filename)
        return ""

def listen_to_user(silent_mode=True, samplerate=16000) -> str:
    """Version automatique pour le CLI."""
    filename = "temp_user_voice.wav"
    try:
        with sd.InputStream(samplerate=samplerate, channels=1, dtype='float32') as stream:
            q = []
            speaking = False
            silence = 0
            while True:
                data, _ = stream.read(int(samplerate * 0.1))
                q.append(data)
                rms = np.sqrt(np.mean(data**2))
                if rms > 0.015:
                    speaking = True
                    silence = 0
                elif speaking:
                    silence += 1
                    if silence > 15: break
                elif len(q) > 100: break
        if not speaking: return ""
        sf.write(filename, np.concatenate(q), samplerate)
        return transcribe_file(filename)
    except: return ""
