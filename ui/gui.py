import customtkinter as ctk
import threading
import sys
import os
import subprocess
import time
import queue
import random
import tkinter as tk

# ── Chemin racine du projet (parent de ui/) ────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import Config
from skills.registry import MENVIS_TOOLS, MENVIS_SCHEMAS
from skills.memory_skills import get_all_memory_context
from skills.voice_input import listen_to_user
import ollama

# ── File de sync Thread IA → Thread UI ────────────────────────────────────
GUI_QUEUE: queue.Queue = queue.Queue()


# ── Fonction speak() patchée pour l'interface graphique ───────────────────
def speak_gui(text: str):
    """Affiche le texte dans la GUI et joue le TTS en arrière-plan."""
    print(f"\n{Config.ASSISTANT_NAME}: {text}")
    GUI_QUEUE.put({"type": "speak", "text": text})
    GUI_QUEUE.put({"type": "anim_start"})

    # Bulle flottante (non-bloquant)
    ui_script = os.path.join(ROOT, "ui", "bubble.py")
    subprocess.Popen(
        [sys.executable, ui_script, text],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    # TTS edge-tts (non-bloquant pour ne pas geler la GUI)
    def _tts():
        try:
            subprocess.run(
                ["edge-tts", "--voice", "fr-FR-HenriNeural", "--text", text, "--play"],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except Exception:
            pass
        GUI_QUEUE.put({"type": "anim_stop"})

    threading.Thread(target=_tts, daemon=True).start()


# ── Assistant embarqué dans la GUI ────────────────────────────────────────
class MenvisAssistantGUI:
    """Version de l'assistant qui utilise speak_gui() à la place de speak()."""

    def __init__(self):
        self.model = Config.MODEL_NAME
        self.tools = MENVIS_TOOLS
        self.schemas = MENVIS_SCHEMAS
        persistent_memory = get_all_memory_context()
        self.messages = [
            {"role": "system", "content": Config.SYSTEM_PROMPT + "\n" + persistent_memory}
        ]

    def ask(self, user_prompt: str):
        self.messages.append({"role": "user", "content": user_prompt})
        print(f"[*] {Config.ASSISTANT_NAME} réfléchit...")

        try:
            response = ollama.chat(
                model=self.model,
                messages=self.messages,
                tools=self.schemas
            )
            message = response["message"]

            if message.get("tool_calls"):
                self.messages.append(message)
                tool_results = []

                for tool_call in message["tool_calls"]:
                    func_name = tool_call["function"]["name"]
                    args = tool_call["function"]["arguments"]
                    func = self.tools.get(func_name)
                    if func:
                        try:
                            result = func(**args)
                        except Exception as e:
                            result = f"Erreur {func_name}: {e}"
                    else:
                        result = f"Outil '{func_name}' non enregistré."

                    tool_results.append(f"• {func_name}: {result}")
                    self.messages.append({"role": "tool", "name": func_name, "content": str(result)})

                final_response = ollama.chat(model=self.model, messages=self.messages)
                final_text = final_response["message"]["content"]
                self.messages.append({"role": "assistant", "content": final_text})
                speak_gui(final_text)

            else:
                final_text = message["content"]
                self.messages.append({"role": "assistant", "content": final_text})
                speak_gui(final_text)

        except Exception as e:
            err = f"Erreur système : {e}"
            speak_gui(err)


# ══════════════════════════════════════════════════════════════════════════
#  Interface Graphique Principale
# ══════════════════════════════════════════════════════════════════════════
class MenvisGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(f"⚡ {Config.ASSISTANT_NAME} — Système OS")
        self.geometry("980x720")
        self.minsize(700, 500)

        self.assistant = MenvisAssistantGUI()
        self.recording_active = False
        self.animating = False

        self._setup_ui()
        self.write_log(f"Système {Config.ASSISTANT_NAME} amorcé. Prêt à obéir.", "SYSTÈME")

        # Démarrage du listener de file d'attente
        self.after(50, self._process_queue)

    # ── Mise en place de l'interface ──────────────────────────────────────
    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ─ Cadre principal ─
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)

        # ─ Historique conversationnel ─
        self.log_box = ctk.CTkTextbox(
            main,
            font=("Inter", 14),
            fg_color="#1e1e2e",
            text_color="#cdd6f4",
            wrap="word",
            corner_radius=12,
        )
        self.log_box.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.log_box.configure(state="disabled")

        # ─ Visualiseur audio (waveform holographique) ─
        wave_frame = ctk.CTkFrame(main, height=130, fg_color="#181825", corner_radius=12)
        wave_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        wave_frame.grid_propagate(False)

        self.canvas = tk.Canvas(wave_frame, height=120, bg="#11111b", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=4, pady=4)

        self.particles = []
        self.after(300, self._init_particles)

        # ─ Zone de saisie ─
        inp = ctk.CTkFrame(self, height=60, fg_color="transparent")
        inp.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        inp.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            inp,
            placeholder_text="Commande Système Override…",
            height=44,
            font=("Inter", 14),
            fg_color="#1e1e2e",
            border_color="#313244",
            corner_radius=10,
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.entry.bind("<Return>", self._send_command)

        self.btn_send = ctk.CTkButton(
            inp, text="⚡ Exécuter", height=44,
            command=self._send_command,
            fg_color="#89b4fa", hover_color="#b4befe",
            font=("Inter", 13, "bold"), corner_radius=10,
        )
        self.btn_send.grid(row=0, column=1, padx=(0, 10))

        self.btn_mic = ctk.CTkButton(
            inp, text="🎙 STANDBY", height=44,
            command=self._toggle_mic,
            fg_color="#f38ba8", hover_color="#eba0ac",
            font=("Inter", 13, "bold"), corner_radius=10,
        )
        self.btn_mic.grid(row=0, column=2)

    # ── Écriture dans l'historique ────────────────────────────────────────
    def write_log(self, text: str, sender: str):
        self.log_box.configure(state="normal")
        if sender == "Vous":
            prefix = "🧑 Vous  › "
            color_tag = "user"
        elif sender == "SYSTÈME":
            prefix = "⚙  SYSTÈME › "
            color_tag = "sys"
        else:
            prefix = f"🤖 {sender}  › "
            color_tag = "ai"

        self.log_box.insert("end", f"{prefix}{text}\n\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ── Boucle de traitement de la file (thread-safe) ─────────────────────
    def _process_queue(self):
        try:
            while True:
                msg = GUI_QUEUE.get_nowait()
                t = msg["type"]
                if t == "speak":
                    self.write_log(msg["text"], Config.ASSISTANT_NAME)
                elif t == "anim_start":
                    self.animating = True
                    self._animate_particles()
                elif t == "anim_stop":
                    self.animating = False
                    self._reset_particles()
                elif t == "user_input":
                    self.write_log(msg["text"], "Vous")
        except queue.Empty:
            pass
        self.after(50, self._process_queue)

    # ── Envoi de commande texte ───────────────────────────────────────────
    def _send_command(self, event=None):
        cmd = self.entry.get().strip()
        if not cmd:
            return
        self.entry.delete(0, "end")
        self.write_log(cmd, "Vous")
        self.entry.configure(state="disabled", placeholder_text="Analyse en cours…")
        self.btn_send.configure(state="disabled")
        threading.Thread(target=self._run_assistant, args=(cmd,), daemon=True).start()

    def _run_assistant(self, text: str):
        try:
            self.assistant.ask(text)
        except Exception as e:
            GUI_QUEUE.put({"type": "speak", "text": f"Erreur fatale : {e}"})
        self.after(0, lambda: self.entry.configure(state="normal", placeholder_text="Commande Système Override…"))
        self.after(0, lambda: self.btn_send.configure(state="normal"))

    # ── Toggle micro ──────────────────────────────────────────────────────
    def _toggle_mic(self):
        if self.recording_active:
            self.recording_active = False
            self.btn_mic.configure(text="🎙 STANDBY", fg_color="#f38ba8", hover_color="#eba0ac")
        else:
            self.recording_active = True
            self.btn_mic.configure(text="🎙 ACTIF", fg_color="#a6e3a1", hover_color="#94e2d5")
            self.write_log("Écoute active…", "SYSTÈME")
            threading.Thread(target=self._voice_loop, daemon=True).start()

    def _voice_loop(self):
        while self.recording_active:
            text = listen_to_user(silent_mode=True)
            if text:
                if any(w in text.lower() for w in ["arrête-toi", "désactiver", "stop menvis"]):
                    GUI_QUEUE.put({"type": "speak", "text": "Passage en mode manuel."})
                    self.after(0, self._toggle_mic)
                    break
                GUI_QUEUE.put({"type": "user_input", "text": text})
                self._run_assistant(text)

    # ══ MOTEUR HOLOGRAPHIQUE (WAVEFORM) ═══════════════════════════════════
    def _init_particles(self):
        self.canvas.delete("all")
        self.particles = []
        w = self.canvas.winfo_width() or 900
        h = self.canvas.winfo_height() or 120
        cy = h / 2
        num_bars = 70
        bar_w = w / num_bars

        for i in range(num_bars):
            x = i * bar_w + bar_w / 2
            line = self.canvas.create_line(x, cy, x, cy, fill="#313244", width=max(2, bar_w * 0.55), capstyle="round")
            self.particles.append((line, x, cy))

    def _animate_particles(self):
        if not self.animating:
            return
        h = self.canvas.winfo_height() or 120
        cy = h / 2
        center = len(self.particles) // 2

        for i, (line, bx, _) in enumerate(self.particles):
            dist = abs(i - center)
            base_amp = max(2, 45 - dist * 1.4)
            amp = random.randint(int(base_amp * 0.15), int(base_amp))
            color = "#f5c2e7" if amp > 28 else "#89dceb" if amp > 12 else "#89b4fa"
            self.canvas.itemconfig(line, fill=color)
            self.canvas.coords(line, bx, cy - amp, bx, cy + amp)

        self.after(55, self._animate_particles)

    def _reset_particles(self):
        h = self.canvas.winfo_height() or 120
        cy = h / 2
        for line, bx, _ in self.particles:
            self.canvas.coords(line, bx, cy - 1, bx, cy + 1)
            self.canvas.itemconfig(line, fill="#313244")


# ── Point d'entrée direct ─────────────────────────────────────────────────
if __name__ == "__main__":
    app = MenvisGUI()
    app.mainloop()
