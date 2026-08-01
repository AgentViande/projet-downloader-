import customtkinter as ctk
import tkinter as tk
from downloader import download_video
import threading
import json
import os
from tkinter import filedialog

# Configuration du thème
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "config.json"

class VideoDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Video Downloader Pro")
        self.geometry("600x380")
        self.resizable(False, False)
        
        self.download_path = self.load_config()

        # Titre
        self.title_label = ctk.CTkLabel(self, text="Video Downloader", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(20, 10))

        # URL Input
        self.url_var = tk.StringVar()
        self.url_entry = ctk.CTkEntry(self, width=450, placeholder_text="Collez le lien de la vidéo ici (YouTube, TikTok, etc.)", textvariable=self.url_var)
        self.url_entry.pack(pady=15)

        # Frame pour les options
        self.options_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.options_frame.pack(pady=10, fill="x", padx=70)

        # Qualité
        self.quality_label = ctk.CTkLabel(self.options_frame, text="Qualité :")
        self.quality_label.pack(side="left", padx=(0, 10))
        
        self.quality_var = ctk.StringVar(value="Meilleure")
        self.quality_menu = ctk.CTkOptionMenu(self.options_frame, values=["Meilleure", "1080p", "720p", "480p", "Audio seulement"], variable=self.quality_var)
        self.quality_menu.pack(side="left")

        # Bouton Dossier
        self.folder_button = ctk.CTkButton(self.options_frame, text="Dossier de destination", command=self.choose_folder, width=150)
        self.folder_button.pack(side="right")
        
        # Affichage du dossier actuel
        self.path_label = ctk.CTkLabel(self, text=f"Dossier : {self.download_path}", text_color="gray", font=ctk.CTkFont(size=11))
        self.path_label.pack(pady=(5, 10))

        # Bouton Télécharger
        self.download_button = ctk.CTkButton(self, text="Télécharger", command=self.start_download, font=ctk.CTkFont(size=15, weight="bold"), height=40, width=200)
        self.download_button.pack(pady=15)

        # Barre de progression
        self.progress_bar = ctk.CTkProgressBar(self, width=450)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10)
        
        # Statut
        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
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
            self.path_label.configure(text=f"Dossier : {self.download_path}")
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
            self.status_label.configure(text="Téléchargement terminé !", text_color="green")
            self.download_button.configure(state="normal")
            
    def start_download(self):
        url = self.url_var.get().strip()
        if not url:
            self.status_label.configure(text="Veuillez entrer une URL valide.", text_color="red")
            return
            
        self.download_button.configure(state="disabled")
        self.status_label.configure(text="Préparation...", text_color="black")
        self.progress_bar.set(0)
        
        quality = self.quality_var.get()
        
        # Lancer le téléchargement dans un thread séparé pour ne pas bloquer l'interface
        thread = threading.Thread(target=self.run_download_thread, args=(url, quality))
        thread.start()
        
    def run_download_thread(self, url, quality):
        try:
            download_video(url, self.download_path, quality, self.progress_hook)
        except Exception as e:
            self.status_label.configure(text=f"Erreur : {str(e)[:50]}...", text_color="red")
            self.download_button.configure(state="normal")

if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.mainloop()
