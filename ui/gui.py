import customtkinter as ctk
import threading
import sys
import os
import time
import queue
import random

# Permet d'importer le cœur de l'App (dossier parent)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main as core_main
from config import Config
from skills.voice_input import listen_to_user

# --- File d'attente pour synchroniser Threads (IA) vers Main GUI ---
GUI_QUEUE = queue.Queue()

# Interception du module Vocal pour afficher le texte et l'animation !
ORIGINAL_SPEAK = core_main.speak
def patched_speak(text):
    GUI_QUEUE.put({"type": "speak", "text": text})
    GUI_QUEUE.put({"type": "anim_start"})
    ORIGINAL_SPEAK(text)
    GUI_QUEUE.put({"type": "anim_stop"})

core_main.speak = patched_speak

class MenvisGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title(f"{Config.ASSISTANT_NAME} - Système OS")
        self.geometry("950x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.assistant = core_main.MenvisAssistant()
        self.recording_active = False
        self.animating = False
        
        self.setup_ui()
        self.write_log(f"Système {Config.ASSISTANT_NAME} amorcé. Prêt à obéir à EndeavourOS.", "SYSTÈME")
        
        # Début du listener d'événements
        self.after(50, self.process_queue)
        
    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # === Zone Centrale (Historique et Hologramme) ===
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Historique
        self.log_box = ctk.CTkTextbox(self.main_frame, font=("Inter", 15), fg_color="#1e1e2e", text_color="#cdd6f4", wrap="word")
        self.log_box.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.log_box.configure(state="disabled")
        
        # HOLOGRAMME / WAVEFORM
        self.canvas_frame = ctk.CTkFrame(self.main_frame, height=120, fg_color="#181825")
        self.canvas_frame.grid(row=1, column=0, sticky="ew")
        # On utilise Tkinter pur pour le Canvas au sein de CustomTkinter
        import tkinter as tk
        self.canvas = tk.Canvas(self.canvas_frame, height=110, bg="#11111b", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Initialisation "Repos" de la particule
        self.particles = []
        self.after(200, self.init_particles) # On attend que la fenêtre soit dessinée
        
        # === Zone Input (Console Manuelle) ===
        self.input_frame = ctk.CTkFrame(self, height=60, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="Commande Système Override...", height=40, font=("Inter", 14), fg_color="#1e1e2e")
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.entry.bind("<Return>", self.send_command)
        
        self.btn_send = ctk.CTkButton(self.input_frame, text="Exécuter", height=40, command=self.send_command, fg_color="#89b4fa", hover_color="#b4befe")
        self.btn_send.grid(row=0, column=1, padx=(0, 10))
        
        # Toggle du micro
        self.btn_mic = ctk.CTkButton(self.input_frame, text="🎙️ MICRO STANDBY", height=40, command=self.toggle_mic, fg_color="#f38ba8", hover_color="#eba0ac")
        self.btn_mic.grid(row=0, column=2)

    def write_log(self, text, sender):
        self.log_box.configure(state="normal")
        # Ajout d'une balise visuelle simple
        if sender == "Vous": prefix = f"[🧑 Vous] : "
        elif sender == "SYSTÈME": prefix = f"[*] "
        else: prefix = f"[🤖 {sender}] : "
        
        self.log_box.insert("end", f"{prefix}{text}\n\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def process_queue(self):
        """Lit la file d'attente pour synchroniser l'IA avec l'interface graphique (Threads -> UI)"""
        try:
            while True:
                msg = GUI_QUEUE.get_nowait()
                if msg["type"] == "speak":
                    self.write_log(msg["text"], Config.ASSISTANT_NAME)
                elif msg["type"] == "anim_start":
                    self.animating = True
                    self.animate_particles()
                elif msg["type"] == "anim_stop":
                    self.animating = False
                    self.reset_particles()
                elif msg["type"] == "user_input":
                    self.write_log(msg["text"], "Vous")
        except queue.Empty:
            pass
        self.after(50, self.process_queue)

    def send_command(self, event=None):
        cmd = self.entry.get().strip()
        if not cmd: return
        self.entry.delete(0, "end")
        self.write_log(cmd, "Vous")
        
        # Verrouille l'input pendant le traitement
        self.entry.configure(state="disabled", placeholder_text="Analyse cognitive en cours...")
        self.btn_send.configure(state="disabled")
        
        threading.Thread(target=self.run_assistant_thread, args=(cmd,), daemon=True).start()

    def run_assistant_thread(self, text):
        try:
            self.assistant.ask(text)
        except Exception as e:
            GUI_QUEUE.put({"type": "speak", "text": f"Erreur fatale de traitement: {e}"})
        
        # Déverrouiller dans l'UI thread via event simulé
        self.after(0, lambda: self.entry.configure(state="normal", placeholder_text="Commande Système Override..."))
        self.after(0, lambda: self.btn_send.configure(state="normal"))

    def toggle_mic(self):
        if self.recording_active:
            self.recording_active = False
            self.btn_mic.configure(text="🎙️ MICRO STANDBY", fg_color="#f38ba8")
        else:
            self.recording_active = True
            self.btn_mic.configure(text="🎙️ MICRO ACTIF", fg_color="#a6e3a1", hover_color="#94e2d5")
            self.write_log("En écoute perpétuelle de l'environnement...", "SYSTÈME")
            threading.Thread(target=self.voice_loop, daemon=True).start()
            
    def voice_loop(self):
        while self.recording_active:
            text = listen_to_user(silent_mode=True)
            if text:
                # Filtrage
                if "arrête-toi" in text.lower() or "désactiver" in text.lower():
                    GUI_QUEUE.put({"type": "speak", "text": "Désactivation du système vocal requise. Passage en mode manuel."})
                    self.after(0, self.toggle_mic)
                    break
                    
                GUI_QUEUE.put({"type": "user_input", "text": text})
                self.run_assistant_thread(text)

    # ================== MOTEUR HOLOGRAPHIQUE (WAVEFORM) ==================
    def init_particles(self):
        self.canvas.delete("all")
        self.particles = []
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        cy = height / 2
        
        # Générer 50 lignes (Spectre)
        num_bars = 60
        bar_width = width / num_bars
        
        for i in range(num_bars):
            x = i * bar_width
            # Ligne initialement plate
            line = self.canvas.create_line(x, cy, x, cy, fill="#89b4fa", width=bar_width*0.6, capstyle="round")
            self.particles.append((line, x, cy))
            
    def animate_particles(self):
        if not self.animating: return
        height = self.canvas.winfo_height()
        cy = height / 2
        
        for i, (line, bx, by) in enumerate(self.particles):
            # Effet de pic au centre
            dist_from_center = abs(i - 30)
            base_amp = max(2, 40 - dist_from_center * 1.5)
            
            # Amplitude aléatoire modulée pour effet de voix (J.A.R.V.I.S)
            amp = random.randint(int(base_amp*0.2), int(base_amp))
            
            # Couleurs dynamiques selon l'intensité (Bleu cyan -> Blanc)
            color = "#f5c2e7" if amp > 25 else "#89dceb" if amp > 10 else "#89b4fa"
            self.canvas.itemconfig(line, fill=color)
            self.canvas.coords(line, bx, cy - amp, bx, cy + amp)
            
        self.after(60, self.animate_particles) # 15 FPS pour fluidité
        
    def reset_particles(self):
        height = self.canvas.winfo_height()
        cy = height / 2
        for i, (line, bx, by) in enumerate(self.particles):
            self.canvas.coords(line, bx, cy - 1, bx, cy + 1)
            self.canvas.itemconfig(line, fill="#313244") # Gris profond éteint

if __name__ == "__main__":
    app = MenvisGUI()
    app.mainloop()
