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
from openai import OpenAI
import json

# ── Chemin racine du projet ────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import Config

# ── Palette Catppuccin Macchiato (Pure Local Edition) ───────────────────
COLORS = {
    "bg": "#24273a",      
    "fg": "#cad3f5",      
    "accent": "#f5bde6",  
    "subtext": "#a5adcb", 
    "danger": "#ed8796",  
    "success": "#a6da95", 
    "wave": "#8aadf4",    
    "card": "#363a4f",    
    "border": "#494d64"   
}

# ── File de sync Thread IA → Thread UI ────────────────────────────────────
GUI_QUEUE: queue.Queue = queue.Queue()
EDGE_TTS_PATH = os.path.join(ROOT, ".venv", "bin", "edge-tts")

def speak_gui(text: str, show_bubble=False):
    """Affiche le texte dans la GUI et joue le TTS."""
    print(f"\n[MENVIS] {text}", flush=True)
    GUI_QUEUE.put({"type": "speak", "text": text})
    GUI_QUEUE.put({"type": "anim_start"})

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
    """Moteur IA via OpenRouter."""
    def __init__(self, callback_ready):
        self.ready = False
        self.callback_ready = callback_ready
        self.messages = []
        self.last_status = ""
        threading.Thread(target=self._late_init, daemon=True).start()

    def _late_init(self):
        try:
            from skills.registry import MENVIS_TOOLS, MENVIS_SCHEMAS, SURVIVAL_TOOLS, SURVIVAL_SCHEMAS
            from skills.memory_skills import get_all_memory_context
            from prompts.system import get_system_prompt
            
            # Détection du mode survie pour la GUI
            if Config.OLLAMA_MODEL == "menvis-lite":
                self.tools_map = SURVIVAL_TOOLS
                self.schemas = SURVIVAL_SCHEMAS
            else:
                self.tools_map = MENVIS_TOOLS
                self.schemas = MENVIS_SCHEMAS
            persistent_memory = get_all_memory_context()
            self.system_instruction = get_system_prompt() + "\n" + persistent_memory

            # Initialisation 100% Locale (Ollama)
            self.model_id = Config.OLLAMA_MODEL
            self.client = OpenAI(
                base_url=Config.OLLAMA_BASE_URL,
                api_key="ollama",
            )
            self.messages = [{'role': 'system', 'content': self.system_instruction}]

            self.ready = True
            GUI_QUEUE.put({"type": "status", "text": "NEXUS ONLINE", "color": COLORS["success"]})
            speak_gui("Menvis est prêt, Chef. Connexion Locale établie.")
        except Exception as e:
            with open("nexus_error.log", "a") as f:
                import traceback
                f.write(f"\n--- INIT ERROR ---\n{traceback.format_exc()}\n")
            GUI_QUEUE.put({"type": "status", "text": "OLLAMA HORS-LIGNE"})

    def ask(self, user_prompt: str):
        if not self.ready: return
        try:
            start_time = time.time()
            GUI_QUEUE.put({"type": "status", "text": "RÉFLEXION [0s]..."})
            
            def _update_reflection():
                while "RÉFLEXION" in self.last_status:
                    elapsed = int(time.time() - start_time)
                    GUI_QUEUE.put({"type": "status", "text": f"RÉFLEXION [{elapsed}s]..."})
                    time.sleep(1)
            
            self.last_status = "RÉFLEXION"
            threading.Thread(target=_update_reflection, daemon=True).start()

            self.messages.append({'role': 'user', 'content': user_prompt})
            
            kwargs = {
                "model": self.model_id,
                "messages": self.messages,
            }
            if self.schemas:
                kwargs["tools"] = [{"type": "function", "function": s} for s in self.schemas]
                
            try:
                response = self.client.chat.completions.create(**kwargs)
            except Exception as e:
                if "400" in str(e) or getattr(e, 'status_code', None) == 400:
                    if "tools" in kwargs:
                        del kwargs["tools"]
                    response = self.client.chat.completions.create(**kwargs)
                else:
                    raise e
                    
            message = response.choices[0].message
            role = message.role
            content = message.content
            tool_calls = message.tool_calls
            
            msg_dict = {'role': role, 'content': content}
            
            while tool_calls:
                msg_dict['tool_calls'] = [
                    {
                        'id': tc.id,
                        'type': 'function',
                        'function': {
                            'name': tc.function.name,
                            'arguments': json.loads(tc.function.arguments)
                        }
                    } for tc in tool_calls
                ]
                self.messages.append(message) # Append object directly
                for tool in tool_calls:
                    func_name = tool.function.name
                    args = json.loads(tool.function.arguments)
                    func = self.tools_map.get(func_name)
                    res = func(**args) if func else "Erreur outil."
                    self.messages.append({
                        'role': 'tool', 
                        'tool_call_id': tool.id,
                        'name': func_name, 
                        'content': str(res)
                    })
                
                response = self.client.chat.completions.create(model=self.model_id, messages=self.messages)
                message = response.choices[0].message
                role = message.role
                content = message.content
                tool_calls = message.tool_calls
                msg_dict = {'role': role, 'content': content}
                
            final_text = content
            self.messages.append({'role': 'assistant', 'content': final_text})
            speak_gui(final_text)
            self.last_status = "NEXUS ONLINE"
            GUI_QUEUE.put({"type": "status", "text": "NEXUS ONLINE"})
                
        except Exception as e:
            self.last_status = "ERREUR"
            with open("nexus_error.log", "a") as f:
                import traceback
                f.write(f"\n--- ASK ERROR ---\n{traceback.format_exc()}\n")
            speak_gui("Coupure du lien. Vérifiez Ollama.")


class MenvisGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title(f"⚡ {Config.ASSISTANT_NAME} - Local Pure Nexus")
        self.geometry("1150x880")
        self.configure(fg_color=COLORS["bg"])

        self.recording_active = False
        self.animating = False
        self.anim_offset = 0

        self._setup_ui()
        self.assistant = MenvisAssistantGUI(self._on_ai_ready)
        self.after(50, self._process_queue)

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.header = ctk.CTkFrame(self, height=70, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=40, pady=(30, 0))
        
        self.title_label = ctk.CTkLabel(self.header, text="MENVIS", font=("Outfit", 30, "bold"), text_color=COLORS["accent"])
        self.title_label.pack(side="left")
        
        self.status_frame = ctk.CTkFrame(self.header, fg_color=COLORS["card"], corner_radius=15)
        self.status_frame.pack(side="right", pady=5)
        self.status_label = ctk.CTkLabel(self.status_frame, text="CONNEXION LOCALE...", font=("Inter", 11, "bold"), text_color=COLORS["subtext"], padx=15, pady=5)
        self.status_label.pack()

        self.chat_container = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=30, border_width=2, border_color=COLORS["border"])
        self.chat_container.grid(row=1, column=0, sticky="nsew", padx=40, pady=30)
        self.chat_container.grid_columnconfigure(0, weight=1)
        self.chat_container.grid_rowconfigure(0, weight=1)

        self.log_box = ctk.CTkTextbox(self.chat_container, font=("Inter", 17), fg_color="transparent", text_color=COLORS["fg"], wrap="word", border_spacing=25)
        self.log_box.grid(row=0, column=0, sticky="nsew")
        self.log_box.configure(state="disabled")

        self.wave_frame = ctk.CTkFrame(self, height=120, fg_color="transparent")
        self.wave_frame.grid(row=2, column=0, sticky="ew", padx=40)
        
        self.wave_canvas = tk.Canvas(self.wave_frame, height=100, bg=COLORS["bg"], highlightthickness=0)
        self.wave_canvas.pack(fill="both", expand=True)
        self.bars = []
        self._init_bars()

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
        self.status_label.configure(text="NEXUS ONLINE", text_color=COLORS["success"])
        speak_gui("Menvis est prêt, Chef. Connexion API établie.")

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
                elif m["type"] == "status": 
                    color = m.get("color", COLORS["subtext"])
                    self.status_label.configure(text=m["text"], text_color=color)
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
        w = 1000 
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
            amp = math.sin(self.anim_offset + i * 0.2) * 35
            h = abs(amp) + random.randint(2, 8)
            self.wave_canvas.coords(l, x, 50-h, x, 50+h)
            color = COLORS["wave"] if h > 25 else COLORS["accent"]
            self.wave_canvas.itemconfig(l, fill=color)
        self.after(40, self._animate)

if __name__ == "__main__":
    print("\n>>> NEXUS VERSION 2.2 (Pure Local) LOADED <<<", flush=True)
    app = MenvisGUI()
    app.mainloop()
