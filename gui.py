import customtkinter as ctk
import tkinter as tk
from downloader import download_video
import threading
import json
import os
from tkinter import filedialog
try:
    import pywinstyles
except ImportError:
    pywinstyles = None

# Configuration du thème
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")

CONFIG_FILE = "config.json"

class VideoDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Video Downloader Pro")
        
        # Fenêtre redimensionnable et plus grande par défaut (Support Plein écran)
        self.geometry("750x550")
        self.minsize(600, 450)
        
        # Application du style Windows 11 Mica si la librairie est dispo
        if pywinstyles:
            try:
                pywinstyles.apply_style(self, "mica")
                # On met le fond de customtkinter en transparent pour laisser passer le Mica
                self.configure(fg_color="transparent")
            except Exception:
                pass
                
        self.download_path = self.load_config()

        # Police moderne Windows 11 (Segoe UI Variable)
        title_font = ctk.CTkFont(family="Segoe UI Variable Display", size=34, weight="bold")
        main_font = ctk.CTkFont(family="Segoe UI Variable Text", size=14)
        button_font = ctk.CTkFont(family="Segoe UI Variable Text", size=16, weight="bold")

        # Container principal centré dynamiquement (pratique pour le plein écran)
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.place(relx=0.5, rely=0.5, anchor="center")

        # Titre
        self.title_label = ctk.CTkLabel(self.main_container, text="Téléchargeur Vidéo", font=title_font)
        self.title_label.pack(pady=(0, 40))

        # Input URL (grande barre de recherche)
        self.url_var = tk.StringVar()
        self.url_entry = ctk.CTkEntry(
            self.main_container, 
            width=550, 
            height=50,
            corner_radius=10,
            font=main_font,
            placeholder_text="Collez un lien YouTube, TikTok, Instagram..."
        )
        self.url_entry.configure(textvariable=self.url_var)
        self.url_entry.pack(pady=(0, 30))

        # Carte pour les options (Style Paramètres Windows 11)
        self.options_card = ctk.CTkFrame(
            self.main_container, 
            corner_radius=12, 
            fg_color=("#f3f3f3", "#2b2b2b"), 
            border_width=1, 
            border_color=("#e5e5e5", "#333333")
        )
        self.options_card.pack(fill="x", pady=(0, 30), ipadx=15, ipady=15)

        # Ligne 1 de la carte : Qualité
        self.quality_frame = ctk.CTkFrame(self.options_card, fg_color="transparent")
        self.quality_frame.pack(fill="x", pady=(5, 10))
        
        self.quality_label = ctk.CTkLabel(self.quality_frame, text="Qualité vidéo", font=main_font)
        self.quality_label.pack(side="left", padx=10)
        
        self.quality_var = ctk.StringVar(value="Meilleure")
        self.quality_menu = ctk.CTkOptionMenu(
            self.quality_frame, 
            values=["Meilleure", "1080p", "720p", "480p", "Audio seulement"], 
            variable=self.quality_var,
            font=main_font,
            corner_radius=6,
            width=160
        )
        self.quality_menu.pack(side="right", padx=10)

        # Ligne de séparation dans la carte
        self.separator = ctk.CTkFrame(self.options_card, height=1, fg_color=("#e5e5e5", "#333333"))
        self.separator.pack(fill="x", padx=10, pady=5)

        # Ligne 2 de la carte : Dossier
        self.folder_frame = ctk.CTkFrame(self.options_card, fg_color="transparent")
        self.folder_frame.pack(fill="x", pady=(10, 5))
        
        # On raccourcit le chemin visuellement s'il est trop long
        display_path = self.download_path
        if len(display_path) > 40:
            display_path = "..." + display_path[-37:]
            
        self.path_label = ctk.CTkLabel(self.folder_frame, text=f"Dossier : {display_path}", font=ctk.CTkFont(family="Segoe UI Variable Text", size=13), text_color="gray")
        self.path_label.pack(side="left", padx=10)
        
        self.folder_button = ctk.CTkButton(
            self.folder_frame, 
            text="Modifier...", 
            command=self.choose_folder, 
            font=main_font, 
            corner_radius=6,
            width=100,
            fg_color="transparent",
            border_width=1,
            text_color=("black", "white"),
            hover_color=("#e5e5e5", "#444444")
        )
        self.folder_button.pack(side="right", padx=10)

        # Bouton Télécharger (Call to action principal)
        self.download_button = ctk.CTkButton(
            self.main_container, 
            text="Télécharger", 
            command=self.start_download, 
            font=button_font, 
            height=50, 
            width=280,
            corner_radius=25 # Bouton très arrondi style Win11
        )
        self.download_button.pack(pady=(10, 15))

        # Barre de progression
        self.progress_bar = ctk.CTkProgressBar(self.main_container, width=550, height=6)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10)
        self.progress_bar.pack_forget() # Caché par défaut pour un look épuré
        
        # Statut
        self.status_label = ctk.CTkLabel(self.main_container, text="", font=main_font, text_color="gray")
        self.status_label.pack()
        
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get("download_path", os.path.join(os.path.expanduser("~"), "Downloads"))
            except:
                pass
        return os.path.join(os.path.expanduser("~"), "Downloads")
        
    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"download_path": self.download_path}, f)

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_path)
        if folder:
            self.download_path = folder
            
            display_path = self.download_path
            if len(display_path) > 40:
                display_path = "..." + display_path[-37:]
            self.path_label.configure(text=f"Dossier : {display_path}")
            self.save_config()

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded_bytes = d.get('downloaded_bytes', 0)
                if total_bytes:
                    percent = downloaded_bytes / total_bytes
                    self.progress_bar.set(percent)
                    percent_str = f"{percent*100:.1f}%"
                    self.status_label.configure(text=f"Téléchargement en cours... {percent_str}")
            except Exception:
                pass
        elif d['status'] == 'finished':
            self.progress_bar.set(1.0)
            self.status_label.configure(text="Téléchargement terminé avec succès ! 🎉", text_color="#107C10") # Vert Microsoft
            self.download_button.configure(state="normal")
            
    def start_download(self):
        url = self.url_var.get().strip()
        if not url:
            self.status_label.configure(text="Veuillez entrer une URL valide.", text_color="#D13438") # Rouge Microsoft
            return
            
        self.download_button.configure(state="disabled")
        self.progress_bar.pack(pady=10) # On affiche la barre
        self.status_label.configure(text="Préparation du téléchargement...", text_color="gray")
        self.progress_bar.set(0)
        
        quality = self.quality_var.get()
        
        # Lancer le téléchargement dans un thread séparé
        thread = threading.Thread(target=self.run_download_thread, args=(url, quality))
        thread.start()
        
    def run_download_thread(self, url, quality):
        try:
            download_video(url, self.download_path, quality, self.progress_hook)
        except Exception as e:
            self.status_label.configure(text=f"Erreur : {str(e)[:50]}...", text_color="#D13438")
            self.download_button.configure(state="normal")

if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.mainloop()
