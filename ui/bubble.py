import tkinter as tk
import sys

def show_bubble(text: str, color: str = "#00ffcc"):
    root = tk.Tk()
    # Ce titre spécifique sera attrapé par Hyprland pour le transformer en widget flottant sans bordure !
    root.title("Menvis")
    
    # Design sombre élégant J.A.R.V.I.S
    bg_color = "#0f1419"
    root.configure(bg=bg_color)
    
    # Contenu du texte
    label = tk.Label(
        root, 
        text=text, 
        font=("Inter", 12, "bold"), 
        fg=color, 
        bg=bg_color, 
        wraplength=350, 
        justify="center"
    )
    label.pack(expand=True, padx=30, pady=25)
    
    # Disparition automatique (autodestruction après 4 secondes)
    root.after(4000, root.destroy)
    root.mainloop()

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "Système Menvis Opérationnel."
    show_bubble(msg)
