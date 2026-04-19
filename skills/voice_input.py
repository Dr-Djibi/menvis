import subprocess
import os

def listen_to_user(silent_mode=True) -> str:
    """Enregistre l'audio (5s) et transcrit. Si silent_mode est True, réduit l'affichage console."""
    filename = "temp_user_voice.wav"
    if not silent_mode:
        print("\n🎧 [En attente de votre voix...]...")
    else:
        print("🎧 [Écoute...] ", end="\r", flush=True)
    
    try:
        subprocess.run(["arecord", "-d", "5", "-f", "cd", "-q", filename], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not silent_mode: print("⏳ Transcription...")
        
        # Import optimisé (chargé uniquement quand nécessaire pour sauver la RAM)
        from faster_whisper import WhisperModel
        
        # Modèle très petit et rapide
        model_size = "tiny"
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        
        segments, info = model.transcribe(filename, beam_size=5, language="fr")
        
        transcription = ""
        for segment in segments:
            transcription += segment.text + " "
            
        os.remove(filename)
        transcription = transcription.strip()
        
        # Ignorer les bruits parasites très courts
        if len(transcription) < 3 or 'Sous-titres par' in transcription:
            return ""
            
        print(f"\nVous (Vocal) : '{transcription}'")
        return transcription
        
    except ImportError:
        print("[!] Faster-Whisper n'est pas installé. (pip install faster-whisper)")
        return ""
    except Exception as e:
        print(f"[!] Erreur d'enregistrement : {e}")
        return ""
