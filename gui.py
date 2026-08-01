import customtkinter as ctk
import tkinter as tk
from downloader import download_video
import threading
import json
import os
from tkinter import filedialog
from PIL import Image
try:
    import pywinstyles
except ImportError:
    pywinstyles = None

# Configuration du thème
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "config.json"

class VideoDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Video Downloader Pro")
        self.geometry("900x600")
        self.minsize(750, 450)
        
        # Application du style Windows 11 Mica
        if pywinstyles:
            try:
                pywinstyles.apply_style(self, "mica")
                self.configure(fg_color="transparent")
            except Exception:
                pass
                
        self.download_path = self.load_config()

        # Polices communes
        self.main_font = ctk.CTkFont(family="Segoe UI Variable Text", size=14)
        
        # === LAYOUT PRINCIPAL (2 Colonnes) ===
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # === SIDEBAR ===
        self.sidebar_expanded = True
        
        # Frame de la sidebar
        self.sidebar_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray90", "gray10"), width=200)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(2, weight=1)
        
        # Top Container (Hamburger + Logo)
        self.top_sidebar_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.top_sidebar_frame.grid(row=0, column=0, padx=10, pady=(20, 10), sticky="w")
        
        # Hamburger Button (Icône native Segoe Fluent)
        self.menu_button = ctk.CTkButton(
            self.top_sidebar_frame, 
            text="\uE700", 
            width=40, 
            height=40, 
            font=ctk.CTkFont(family="Segoe Fluent Icons", size=18), 
            fg_color="transparent", 
            text_color=("black", "white"), 
            hover_color=("gray80", "gray20"), 
            command=self.toggle_sidebar
        )
        self.menu_button.pack(side="left")
        
        # Chargement des images couleur (Icons8)
        try:
            self.icon_download = ctk.CTkImage(Image.open("icon_download.png"), size=(24, 24))
            self.icon_logo = ctk.CTkImage(Image.open("icon_logo.png"), size=(28, 28))
        except Exception:
            self.icon_download = None
            self.icon_logo = None

        # Logo Label
        self.logo_label = ctk.CTkLabel(
            self.top_sidebar_frame, 
            text=" Video Pro", 
            image=self.icon_logo,
            compound="left",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=18, weight="bold")
        )
        self.logo_label.pack(side="left", padx=(10, 10))
        
        # Bouton Onglet 1 (Télécharger)
        self.tab_download_btn = ctk.CTkButton(
            self.sidebar_frame, 
            text=" Télécharger", 
            image=self.icon_download,
            compound="left",
            anchor="w", 
            fg_color=("gray80", "gray20"),
            text_color=("black", "white"),
            hover_color=("gray70", "gray30"),
            height=45, 
            width=180,
            font=ctk.CTkFont(family="Segoe UI Variable Text", size=14)
        )
        self.tab_download_btn.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        # (Futurs onglets ici: row=2, row=3, etc.)
        
        # === MAIN VIEW ===
        self.main_view = ctk.CTkFrame(self, fg_color="transparent")
        self.main_view.grid(row=0, column=1, sticky="nsew")
        
        # === INITIALISATION DE L'ONGLET ===
        self.setup_download_tab()
        
    def toggle_sidebar(self):
        if self.sidebar_expanded:
            # Action: Rétracter
            self.logo_label.pack_forget()
            self.tab_download_btn.configure(
                text="", 
                width=40, 
                anchor="center"
            )
            self.sidebar_expanded = False
        else:
            # Action: Déployer
            self.logo_label.pack(side="left", padx=(10, 10))
            self.tab_download_btn.configure(
                text=" Télécharger", 
                width=180, 
                anchor="w",
                font=ctk.CTkFont(family="Segoe UI Variable Text", size=14)
            )
            self.sidebar_expanded = True
            
    def setup_download_tab(self):
        # Container principal de l'onglet, centré
        self.download_container = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.download_container.place(relx=0.5, rely=0.5, anchor="center")

        title_font = ctk.CTkFont(family="Segoe UI Variable Display", size=34, weight="bold")
        button_font = ctk.CTkFont(family="Segoe UI Variable Text", size=16, weight="bold")

        self.title_label = ctk.CTkLabel(self.download_container, text="Télécharger une vidéo", font=title_font)
        self.title_label.pack(pady=(0, 40))

        self.url_var = tk.StringVar()
        self.url_entry = ctk.CTkEntry(
            self.download_container, 
            width=550, 
            height=50,
            corner_radius=10,
            font=self.main_font,
            placeholder_text="Collez un lien YouTube, TikTok, Instagram..."
        )
        self.url_entry.configure(textvariable=self.url_var)
        self.url_entry.pack(pady=(0, 30))

        self.options_card = ctk.CTkFrame(
            self.download_container, 
            corner_radius=12, 
            fg_color=("#f3f3f3", "#2b2b2b"), 
            border_width=1, 
            border_color=("#e5e5e5", "#333333")
        )
        self.options_card.pack(fill="x", pady=(0, 30), ipadx=15, ipady=15)

        self.quality_frame = ctk.CTkFrame(self.options_card, fg_color="transparent")
        self.quality_frame.pack(fill="x", pady=(5, 10))
        
        self.quality_label = ctk.CTkLabel(self.quality_frame, text="Qualité vidéo", font=self.main_font)
        self.quality_label.pack(side="left", padx=10)
        
        self.quality_var = ctk.StringVar(value="Meilleure")
        self.quality_menu = ctk.CTkOptionMenu(
            self.quality_frame, 
            values=["Meilleure", "1080p", "720p", "480p", "Audio seulement"], 
            variable=self.quality_var,
            font=self.main_font,
            corner_radius=6,
            width=160
        )
        self.quality_menu.pack(side="right", padx=10)

        self.separator = ctk.CTkFrame(self.options_card, height=1, fg_color=("#e5e5e5", "#333333"))
        self.separator.pack(fill="x", padx=10, pady=5)

        self.folder_frame = ctk.CTkFrame(self.options_card, fg_color="transparent")
        self.folder_frame.pack(fill="x", pady=(10, 5))
        
        display_path = self.download_path
        if len(display_path) > 40:
            display_path = "..." + display_path[-37:]
            
        self.path_label = ctk.CTkLabel(self.folder_frame, text=f"Dossier : {display_path}", font=ctk.CTkFont(family="Segoe UI Variable Text", size=13), text_color="gray")
        self.path_label.pack(side="left", padx=10)
        
        self.folder_button = ctk.CTkButton(
            self.folder_frame, 
            text="Modifier...", 
            command=self.choose_folder, 
            font=self.main_font, 
            corner_radius=6,
            width=100,
            fg_color="transparent",
            border_width=1,
            text_color=("black", "white"),
            hover_color=("#e5e5e5", "#444444")
        )
        self.folder_button.pack(side="right", padx=10)

        self.download_button = ctk.CTkButton(
            self.download_container, 
            text="Télécharger", 
            command=self.start_download, 
            font=button_font, 
            height=50, 
            width=280,
            corner_radius=25
        )
        self.download_button.pack(pady=(10, 15))

        self.progress_bar = ctk.CTkProgressBar(self.download_container, width=550, height=6)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10)
        self.progress_bar.pack_forget()
        
        self.status_label = ctk.CTkLabel(self.download_container, text="", font=self.main_font, text_color="gray")
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
            self.status_label.configure(text="Téléchargement terminé avec succès ! 🎉", text_color="#107C10")
            self.download_button.configure(state="normal")
            
    def start_download(self):
        url = self.url_var.get().strip()
        if not url:
            self.status_label.configure(text="Veuillez entrer une URL valide.", text_color="#D13438")
            return
            
        self.download_button.configure(state="disabled")
        self.progress_bar.pack(pady=10)
        self.status_label.configure(text="Préparation du téléchargement...", text_color="gray")
        self.progress_bar.set(0)
        
        quality = self.quality_var.get()
        
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
