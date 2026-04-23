import os
import sounddevice as sd
import soundfile as sf
import numpy as np

def listen_to_user(silent_mode=True, samplerate=16000) -> str:
    """Enregistre l'audio jusqu'à ce qu'un silence soit détecté via sounddevice (compatible PipeWire/Pulse)."""
    filename = "temp_user_voice.wav"
    if not silent_mode:
        print("\n🎧 [En attente de votre voix...]...")
    else:
        print("🎧 [Calibration micro...] ", end="\r", flush=True)
    
    try:
        block_duration = 0.1  # 100ms par bloc
        block_size = int(samplerate * block_duration)
        
        q = []
        is_speaking = False
        silence_frames = 0
        max_silence_blocks = int(1.5 / block_duration) # 1.5 sec de silence pour couper
        max_wait_blocks = int(10.0 / block_duration) # Au bout de 10 sec sans voix, on coupe
        
        with sd.InputStream(samplerate=samplerate, channels=1, dtype='float32') as stream:
            # 1. Calibration rapide (0.5s)
            calibration_data = []
            for _ in range(5):
                data, _ = stream.read(block_size)
                calibration_data.append(data)
            baseline_rms = np.sqrt(np.mean(np.concatenate(calibration_data)**2))
            threshold = max(baseline_rms * 2.5, 0.015) # Dynamique
            
            if silent_mode:
                print("🎧 [Écoute automatique...] ", end="\r", flush=True)

            # 2. Boucle d'enregistrement
            while True:
                data, _ = stream.read(block_size)
                q.append(data)
                rms = np.sqrt(np.mean(data**2))
                
                if rms > threshold:
                    if not is_speaking:
                        is_speaking = True
                        if not silent_mode: print("🎙️ [Voix détectée]")
                    silence_frames = 0
                else:
                    if is_speaking:
                        silence_frames += 1
                        if silence_frames > max_silence_blocks:
                            if not silent_mode: print("\n🤫 [Silence, arrêt]")
                            break
                    else:
                        if len(q) > max_wait_blocks:
                            # 10 secondes d'attente sans rien dire, on abandonne
                            break
                            
        audio_data = np.concatenate(q, axis=0)
        
        # Si on n'a jamais parlé, on annule
        if not is_speaking:
            return ""

        sf.write(filename, audio_data, samplerate)
        
        if not silent_mode: print("⏳ Transcription...")
        
        from faster_whisper import WhisperModel
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, info = model.transcribe(filename, beam_size=5, language="fr", vad_filter=True)
        
        transcription = " ".join([segment.text for segment in segments]).strip()
            
        if os.path.exists(filename):
            os.remove(filename)
            
        if not transcription:
            return ""

        print(" " * 40, end="\r") 
        print(f"Vous : {transcription}")
        return transcription
        
    except ImportError:
        print("[!] Faster-Whisper, sounddevice ou soundfile n'est pas installé.")
        return ""
    except Exception as e:
        print(f"[!] Erreur d'enregistrement micro : {e}")
        return ""
