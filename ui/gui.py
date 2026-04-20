import customtkinter as ctk
import threading
import sys
import os
import subprocess
import time
import queue
import random
import tkinter as tk
import math

# ── Chemin racine du projet ────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import Config

# ── Palette Catppuccin Macchiato (Holographic Edition) ───────────────────
COLORS = {
    "bg": "#24273a",      # Fond principal
    "fg": "#cad3f5",      # Texte
    "accent": "#8aadf4",  # Bleu Saphir (Glow)
    "subtext": "#a5adcb", # Gris bleu
    "danger": "#ed8796",  # Rose/Rouge
    "success": "#a6da95", # Vert
    "wave": "#f5bde6",    # Rose Hologramme
    "card": "#363a4f",    # Conteneur
    "border": "#494d64"   # Bordures fines
}

# ── File de sync Thread IA → Thread UI ────────────────────────────────────
GUI_QUEUE: queue.Queue = queue.Queue()
EDGE_TTS_PATH = os.path.join(ROOT, ".venv", "bin", "edge-tts")

def speak_gui(text: str, show_bubble=False):
    """Affiche le texte dans la GUI et joue le TTS."""
    print(f"\n[MENVIS] {text}")
    GUI_QUEUE.put({"type": "speak", "text": text})
    GUI_QUEUE.put({"type": "anim_start"})

    if show_bubble:
        ui_script = os.path.join(ROOT, "ui", "bubble.py")
        subprocess.Popen([sys.executable, ui_script, text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _tts():
        try:
            if not os.path.exists(EDGE_TTS_PATH): return
            process = subprocess.Popen(
                [EDGE_TTS_PATH, "--voice", "fr-FR-HenriNeural", "--text", text],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
            )
            subprocess.run(["mpv", "--no-terminal", "--ao=pulse,pipewire,alsa", "--cache=yes", "-"], 
                         stdin=process.stdout, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception: pass
        GUI_QUEUE.put({"type": "anim_stop"})
    threading.Thread(target=_tts, daemon=True).start()

class MenvisAssistantGUI:
    """Moteur IA proactif v3.0 Holographic (Gemini Flash Stable)."""
    def __init__(self, callback_ready):
        self.ready = False
        self.callback_ready = callback_ready
        self.client = None
        threading.Thread(target=self._late_init, daemon=True).start()

    def _late_init(self):
        try:
            from google import genai
            from google.genai import types
            from skills.registry import MENVIS_TOOLS, MENVIS_SCHEMAS
            from skills.memory_skills import get_all_memory_context
            
            api_key = Config.GEMINI_API_KEY
            if not api_key:
                self.ready = "NEED_KEY"
                self.callback_ready()
                return

            self.client = genai.Client(api_key=api_key)
            self.model_id = "gemini-flash-latest" # Stable & Gratuit (1500 RPM)
            self.tools_map = MENVIS_TOOLS
            
            gemini_functions = []
            for s in MENVIS_SCHEMAS:
                f = s.get('function', s)
                gemini_functions.append({
                    'name': f['name'],
                    'description': f['description'],
                    'parameters': f['parameters']
                })
            
            self.gemini_tools = [{'function_declarations': gemini_functions}]
            persistent_memory = get_all_memory_context()
            self.system_instruction = Config.SYSTEM_PROMPT + "\n" + persistent_memory
            
            self.chat_session = self.client.chats.create(
                model=self.model_id,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    tools=self.gemini_tools
                )
            )
            self.ready = True
            self.callback_ready()
        except Exception as e:
            GUI_QUEUE.put({"type": "status", "text": "RECONNEXION DU NEXUS..."})
            print(f"[ERREUR] {e}")

    def ask(self, user_prompt: str):
        if not self.ready: return
        try:
            GUI_QUEUE.put({"type": "status", "text": "ANALYSE EN COURS..."})
            response = self.chat_session.send_message(user_prompt)
            
            while response.candidates[0].content.parts and response.candidates[0].content.parts[0].function_call:
                tool_results = []
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        func_name = part.function_call.name
                        args = part.function_call.args
                        func = self.tools_map.get(func_name)
                        if func:
                            try: res = func(**args)
                            except Exception as e: res = f"Erreur : {e}"
                        else: res = "Capacité indisponible."
                        
                        from google.genai import types
                        tool_results.append(types.Part.from_function_response(
                            name=func_name,
                            response={'result': str(res)}
                        ))
                response = self.chat_session.send_message(tool_results)

            final_text = response.text
            if final_text:
                GUI_QUEUE.put({"type": "status", "text": "MENVIS CONNECTÉ"})
                speak_gui(final_text)
            
        except Exception as e:
            msg = "Pause nécessaire, Chef." if "429" in str(e) else "Signal perturbé."
            speak_gui(msg)

class MenvisGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title(f"⚡ {Config.ASSISTANT_NAME} Holographic Edition")
        self.geometry("1150x880")
        self.configure(fg_color=COLORS["bg"])

        self.assistant = MenvisAssistantGUI(self._on_ai_ready)
        self.recording_active = False
        self.animating = False
        self.anim_offset = 0

        self._setup_ui()
        self.after(50, self._process_queue)

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Header Bar ──────────────────────────────────────────────────
        self.header = ctk.CTkFrame(self, height=70, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=40, pady=(30, 0))
        
        self.title_label = ctk.CTkLabel(self.header, text="MENVIS", font=("Outfit", 30, "bold"), text_color=COLORS["accent"])
        self.title_label.pack(side="left")
        
        self.status_frame = ctk.CTkFrame(self.header, fg_color=COLORS["card"], corner_radius=15)
        self.status_frame.pack(side="right", pady=5)
        self.status_label = ctk.CTkLabel(self.status_frame, text="INITIALISATION...", font=("Inter", 11, "bold"), text_color=COLORS["subtext"], padx=15, pady=5)
        self.status_label.pack()

        # ── Chat Area (Card View) ─────────────────────────────────────────
        self.chat_container = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=30, border_width=2, border_color=COLORS["border"])
        self.chat_container.grid(row=1, column=0, sticky="nsew", padx=40, pady=30)
        self.chat_container.grid_columnconfigure(0, weight=1)
        self.chat_container.grid_rowconfigure(0, weight=1)

        self.log_box = ctk.CTkTextbox(self.chat_container, font=("Inter", 17), fg_color="transparent", text_color=COLORS["fg"], wrap="word", border_spacing=25)
        self.log_box.grid(row=0, column=0, sticky="nsew")
        self.log_box.configure(state="disabled")

        # ── Waveform / Particles Area ─────────────────────────────────────
        self.wave_frame = ctk.CTkFrame(self, height=120, fg_color="transparent")
        self.wave_frame.grid(row=2, column=0, sticky="ew", padx=40)
        
        self.wave_canvas = tk.Canvas(self.wave_frame, height=100, bg=COLORS["bg"], highlightthickness=0)
        self.wave_canvas.pack(fill="both", expand=True)
        self.bars = []
        self._init_bars()

        # ── Input Area ────────────────────────────────────────────────────
        self.input_area = ctk.CTkFrame(self, height=120, fg_color="transparent")
        self.input_area.grid(row=3, column=0, sticky="ew", padx=40, pady=(0, 40))
        self.input_area.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(self.input_area, placeholder_text="Commandez votre mentor virtuel...", 
                                  height=65, corner_radius=25, border_width=2, border_color=COLORS["border"], 
                                  fg_color=COLORS["card"], font=("Inter", 16))
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 20))
        self.entry.bind("<Return>", self._send_cmd)

        self.btn_mic = ctk.CTkButton(self.input_area, text="🎙️", width=90, height=65, 
                                     corner_radius=25, fg_color=COLORS["accent"], 
                                     hover_color="#5e81ac", font=("Inter", 26), command=self._toggle_mic)
        self.btn_mic.grid(row=0, column=1)

    def _on_ai_ready(self):
        if self.assistant.ready == "NEED_KEY":
            self.status_label.configure(text="CLE API MANQUANTE", text_color=COLORS["danger"])
        else:
            self.status_label.configure(text="NEXUS PRÊT", text_color=COLORS["success"])
            speak_gui("Menvis est prêt, Chef. Que puis-je faire pour vous ?")

    def write_log(self, text, sender):
        self.log_box.configure(state="normal")
        name = f" {sender.upper()} "
        self.log_box.insert("end", f"\n{name}\n", ("name",))
        self.log_box.insert("end", f"{text}\n")
        self.log_box.tag_config("name", foreground=COLORS["accent"])
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _process_queue(self):
        try:
            while True:
                m = GUI_QUEUE.get_nowait()
                if m["type"] == "speak": self.write_log(m["text"], Config.ASSISTANT_NAME)
                elif m["type"] == "status": self.status_label.configure(text=m["text"])
                elif m["type"] == "anim_start": self.animating = True; self._animate()
                elif m["type"] == "anim_stop": self.animating = False
        except queue.Empty: pass
        self.after(50, self._process_queue)

    def _send_cmd(self, event=None):
        txt = self.entry.get().strip()
        if not txt: return
        self.entry.delete(0, "end")
        self.write_log(txt, "VOUS")
        threading.Thread(target=self.assistant.ask, args=(txt,), daemon=True).start()

    def _toggle_mic(self):
        if self.recording_active:
            self.recording_active = False
            self.btn_mic.configure(fg_color=COLORS["accent"])
        else:
            self.recording_active = True
            self.btn_mic.configure(fg_color=COLORS["success"])
            threading.Thread(target=self._mic_loop, daemon=True).start()

    def _mic_loop(self):
        try:
            from skills.voice_input import listen_to_user
            while self.recording_active:
                t = listen_to_user(silent_mode=True)
                if t:
                    self.write_log(t, "VOCAL")
                    threading.Thread(target=self.assistant.ask, args=(t,), daemon=True).start()
        except Exception: self.recording_active = False

    def _init_bars(self):
        w = 1000 # Largeur fixe pour l'onde
        for i in range(80):
            x = (w / 80) * i + 40
            line = self.wave_canvas.create_line(x, 49, x, 51, fill=COLORS["border"], width=3, capstyle="round")
            self.bars.append((line, x))

    def _animate(self):
        if not self.animating: 
            for l, x in self.bars: self.wave_canvas.coords(l, x, 49, x, 51)
            return
        
        self.anim_offset += 0.3
        for i, (l, x) in enumerate(self.bars):
            # Onde sinusoïdale complexe
            amp = math.sin(self.anim_offset + i * 0.2) * 35
            h = abs(amp) + random.randint(2, 8)
            self.wave_canvas.coords(l, x, 50-h, x, 50+h)
            
            # Couleur changeante selon l'intensité
            color = COLORS["wave"] if h > 25 else COLORS["accent"]
            self.wave_canvas.itemconfig(l, fill=color)
            
        self.after(40, self._animate)

if __name__ == "__main__":
    app = MenvisGUI()
    app.mainloop()
