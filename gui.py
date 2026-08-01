import customtkinter as ctk
import tkinter as tk
from downloader import download_video, download_channel
import threading
import json
import os
import time
from datetime import datetime
from tkinter import filedialog
from PIL import Image

try:
    import pywinstyles
except ImportError:
    pywinstyles = None

try:
    import pystray
except ImportError:
    pystray = None

# Configuration du thème
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "config.json"
TRACKING_FILE = "tracking.json"

class VideoDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Video Downloader Pro")
        self.geometry("900x650")
        self.minsize(750, 500)
        
        # Minimiser dans la barre des tâches (System Tray) au lieu de fermer
        self.protocol('WM_DELETE_WINDOW', self.hide_window)
        self.tray_icon = None
        
        if pywinstyles:
            try:
                pywinstyles.apply_style(self, "mica")
                self.configure(fg_color="transparent")
            except Exception:
                pass
                
        self.download_path = self.load_config()
        self.tracking_data = self.load_tracking()

        self.main_font = ctk.CTkFont(family="Segoe UI Variable Text", size=14)
        
        # === LAYOUT PRINCIPAL (2 Colonnes) ===
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # === SIDEBAR ===
        self.sidebar_expanded = True
        self.sidebar_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray90", "gray10"), width=200)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(3, weight=1)
        
        self.top_sidebar_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.top_sidebar_frame.grid(row=0, column=0, padx=10, pady=(20, 10), sticky="w")
        
        self.menu_button = ctk.CTkButton(
            self.top_sidebar_frame, text="\uE700", width=40, height=40, 
            font=ctk.CTkFont(family="Segoe Fluent Icons", size=18), 
            fg_color="transparent", text_color=("black", "white"), 
            hover_color=("gray80", "gray20"), command=self.toggle_sidebar
        )
        self.menu_button.pack(side="left")
        
        try:
            self.icon_download = ctk.CTkImage(Image.open("icon_download.png"), size=(24, 24))
            self.icon_logo = ctk.CTkImage(Image.open("icon_logo.png"), size=(28, 28))
            self.icon_auto = ctk.CTkImage(Image.open("icon_auto.png"), size=(24, 24))
        except Exception:
            self.icon_download = None
            self.icon_logo = None
            self.icon_auto = None

        self.logo_label = ctk.CTkLabel(
            self.top_sidebar_frame, text=" Video Pro", image=self.icon_logo,
            compound="left", font=ctk.CTkFont(family="Segoe UI Variable Display", size=18, weight="bold")
        )
        self.logo_label.pack(side="left", padx=(10, 10))
        
        # Onglet 1: Télécharger
        self.tab_download_btn = ctk.CTkButton(
            self.sidebar_frame, text=" Télécharger", image=self.icon_download,
            compound="left", anchor="w", fg_color=("gray80", "gray20"),
            text_color=("black", "white"), hover_color=("gray70", "gray30"),
            height=45, width=180, font=self.main_font,
            command=self.show_download_tab
        )
        self.tab_download_btn.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        # Onglet 2: Suivi Auto
        self.tab_auto_btn = ctk.CTkButton(
            self.sidebar_frame, text=" Suivi Auto", image=self.icon_auto,
            compound="left", anchor="w", fg_color="transparent",
            text_color=("black", "white"), hover_color=("gray70", "gray30"),
            height=45, width=180, font=self.main_font,
            command=self.show_auto_tab
        )
        self.tab_auto_btn.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        # === MAIN VIEW ===
        self.main_view = ctk.CTkFrame(self, fg_color="transparent")
        self.main_view.grid(row=0, column=1, sticky="nsew")
        
        # Vues
        self.setup_download_tab()
        self.setup_auto_tab()
        
        # Afficher le premier onglet par défaut
        self.show_download_tab()
        
        # Lancer le worker de fond
        self.is_running = True
        self.bg_thread = threading.Thread(target=self.background_worker, daemon=True)
        self.bg_thread.start()

    # --- GESTION DES ONGLETS ---
    def show_download_tab(self):
        self.auto_container.place_forget()
        self.download_container.place(relx=0.5, rely=0.5, anchor="center")
        self.tab_download_btn.configure(fg_color=("gray80", "gray20"))
        self.tab_auto_btn.configure(fg_color="transparent")
        
    def show_auto_tab(self):
        self.download_container.place_forget()
        self.auto_container.place(relx=0.5, rely=0.5, anchor="center")
        self.tab_auto_btn.configure(fg_color=("gray80", "gray20"))
        self.tab_download_btn.configure(fg_color="transparent")

    # --- SIDEBAR TOGGLE ---
    def toggle_sidebar(self):
        if self.sidebar_expanded:
            self.logo_label.pack_forget()
            self.tab_download_btn.configure(text="", width=40, anchor="center")
            self.tab_auto_btn.configure(text="", width=40, anchor="center")
            self.sidebar_expanded = False
        else:
            self.logo_label.pack(side="left", padx=(10, 10))
            self.tab_download_btn.configure(text=" Télécharger", width=180, anchor="w")
            self.tab_auto_btn.configure(text=" Suivi Auto", width=180, anchor="w")
            self.sidebar_expanded = True

    # --- SETUP ONGLET TÉLÉCHARGEMENT ---
    def setup_download_tab(self):
        self.download_container = ctk.CTkFrame(self.main_view, fg_color="transparent")
        
        title_font = ctk.CTkFont(family="Segoe UI Variable Display", size=34, weight="bold")
        button_font = ctk.CTkFont(family="Segoe UI Variable Text", size=16, weight="bold")

        ctk.CTkLabel(self.download_container, text="Télécharger une vidéo", font=title_font).pack(pady=(0, 40))

        self.url_var = tk.StringVar()
        ctk.CTkEntry(
            self.download_container, width=550, height=50, corner_radius=10, font=self.main_font,
            placeholder_text="Collez un lien YouTube, TikTok, Instagram...", textvariable=self.url_var
        ).pack(pady=(0, 30))

        options_card = ctk.CTkFrame(self.download_container, corner_radius=12, fg_color=("#f3f3f3", "#2b2b2b"), border_width=1, border_color=("#e5e5e5", "#333333"))
        options_card.pack(fill="x", pady=(0, 30), ipadx=15, ipady=15)

        q_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        q_frame.pack(fill="x", pady=(5, 10))
        ctk.CTkLabel(q_frame, text="Qualité vidéo", font=self.main_font).pack(side="left", padx=10)
        self.quality_var = ctk.StringVar(value="Meilleure")
        ctk.CTkOptionMenu(q_frame, values=["Meilleure", "1080p", "720p", "480p", "Audio seulement"], variable=self.quality_var, font=self.main_font, corner_radius=6, width=160).pack(side="right", padx=10)

        ctk.CTkFrame(options_card, height=1, fg_color=("#e5e5e5", "#333333")).pack(fill="x", padx=10, pady=5)

        f_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        f_frame.pack(fill="x", pady=(10, 5))
        
        display_path = self.download_path
        if len(display_path) > 40: display_path = "..." + display_path[-37:]
        self.path_label = ctk.CTkLabel(f_frame, text=f"Dossier : {display_path}", font=ctk.CTkFont(family="Segoe UI Variable Text", size=13), text_color="gray")
        self.path_label.pack(side="left", padx=10)
        
        ctk.CTkButton(
            f_frame, text="Modifier...", command=self.choose_folder, font=self.main_font, corner_radius=6,
            width=100, fg_color="transparent", border_width=1, text_color=("black", "white"), hover_color=("#e5e5e5", "#444444")
        ).pack(side="right", padx=10)

        self.download_button = ctk.CTkButton(self.download_container, text="Télécharger", command=self.start_download, font=button_font, height=50, width=280, corner_radius=25)
        self.download_button.pack(pady=(10, 15))

        self.progress_bar = ctk.CTkProgressBar(self.download_container, width=550, height=6)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10)
        self.progress_bar.pack_forget()
        
        self.status_label = ctk.CTkLabel(self.download_container, text="", font=self.main_font, text_color="gray")
        self.status_label.pack()

    # --- SETUP ONGLET SUIVI AUTO ---
    def setup_auto_tab(self):
        self.auto_container = ctk.CTkFrame(self.main_view, fg_color="transparent")
        title_font = ctk.CTkFont(family="Segoe UI Variable Display", size=34, weight="bold")
        
        ctk.CTkLabel(self.auto_container, text="Suivi Automatique", font=title_font).pack(pady=(0, 20))
        ctk.CTkLabel(self.auto_container, text="Le logiciel surveillera ces chaînes et téléchargera les nouvelles vidéos en arrière-plan.", text_color="gray", font=self.main_font).pack(pady=(0, 20))

        # Carte d'ajout
        add_card = ctk.CTkFrame(self.auto_container, corner_radius=12, fg_color=("#f3f3f3", "#2b2b2b"), border_width=1, border_color=("#e5e5e5", "#333333"))
        add_card.pack(fill="x", pady=(0, 20), ipadx=15, ipady=15)
        
        # Ligne 1 : URL
        url_frame = ctk.CTkFrame(add_card, fg_color="transparent")
        url_frame.pack(fill="x", pady=5)
        self.auto_url_var = tk.StringVar()
        ctk.CTkEntry(url_frame, textvariable=self.auto_url_var, placeholder_text="Lien de la chaîne (YouTube, TikTok...)", width=400).pack(side="left", padx=10)
        
        # Ligne 2 : Paramètres
        params_frame = ctk.CTkFrame(add_card, fg_color="transparent")
        params_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(params_frame, text="Depuis le :").pack(side="left", padx=(10, 5))
        self.auto_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ctk.CTkEntry(params_frame, textvariable=self.auto_date_var, width=100).pack(side="left", padx=5)
        
        ctk.CTkLabel(params_frame, text="Vérifier toutes les (heures) :").pack(side="left", padx=(20, 5))
        self.auto_interval_var = tk.StringVar(value="6")
        ctk.CTkEntry(params_frame, textvariable=self.auto_interval_var, width=50).pack(side="left", padx=5)
        
        ctk.CTkButton(params_frame, text="Ajouter", command=self.add_tracking, width=100, corner_radius=6).pack(side="right", padx=10)

        # Liste des chaînes
        self.channels_frame = ctk.CTkScrollableFrame(self.auto_container, width=550, height=180, fg_color="transparent")
        self.channels_frame.pack(pady=10)
        
        # Bouton manuel et statut
        bottom_frame = ctk.CTkFrame(self.auto_container, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=10)
        
        self.auto_status_label = ctk.CTkLabel(bottom_frame, text="", text_color="gray", font=self.main_font)
        self.auto_status_label.pack(side="left", padx=10)
        
        ctk.CTkButton(bottom_frame, text="Vérifier maintenant", command=self.force_check, corner_radius=20).pack(side="right", padx=10)
        
        self.refresh_tracking_list()

    # --- LOGIQUE TRACKING ---
    def load_tracking(self):
        if os.path.exists(TRACKING_FILE):
            try:
                with open(TRACKING_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []

    def save_tracking(self):
        with open(TRACKING_FILE, 'w') as f:
            json.dump(self.tracking_data, f)

    def add_tracking(self):
        url = self.auto_url_var.get().strip()
        if not url: return
        self.tracking_data.append({
            "url": url,
            "date_after": self.auto_date_var.get(),
            "interval": float(self.auto_interval_var.get()),
            "last_checked": 0
        })
        self.save_tracking()
        self.auto_url_var.set("")
        self.refresh_tracking_list()
        
    def remove_tracking(self, index):
        if 0 <= index < len(self.tracking_data):
            del self.tracking_data[index]
            self.save_tracking()
            self.refresh_tracking_list()

    def refresh_tracking_list(self):
        for widget in self.channels_frame.winfo_children():
            widget.destroy()
            
        for i, data in enumerate(self.tracking_data):
            f = ctk.CTkFrame(self.channels_frame, corner_radius=8, fg_color=("#e0e0e0", "#303030"))
            f.pack(fill="x", pady=5, padx=5, ipadx=10, ipady=10)
            
            url_short = data['url']
            if len(url_short) > 40: url_short = url_short[:40] + "..."
            
            ctk.CTkLabel(f, text=url_short, font=ctk.CTkFont(weight="bold")).pack(side="left")
            ctk.CTkLabel(f, text=f" (Toutes les {data['interval']}h)", text_color="gray").pack(side="left")
            
            ctk.CTkButton(f, text="X", width=30, fg_color="#D13438", hover_color="#A80000", command=lambda idx=i: self.remove_tracking(idx)).pack(side="right")

    # --- BACKGROUND WORKER ---
    def force_check(self):
        self.auto_status_label.configure(text="Vérification forcée en cours...", text_color="blue")
        threading.Thread(target=self.run_checks, args=(True,), daemon=True).start()

    def background_worker(self):
        while self.is_running:
            self.run_checks()
            time.sleep(60) # Vérifier chaque minute si une chaîne a dépassé son intervalle

    def run_checks(self, force=False):
        now = time.time()
        for data in self.tracking_data:
            interval_seconds = data['interval'] * 3600
            if force or (now - data.get('last_checked', 0) > interval_seconds):
                try:
                    # Met à jour le status UI
                    self.after(0, lambda u=data['url']: self.auto_status_label.configure(text=f"Vérification: {u[:30]}...", text_color="black"))
                    
                    download_channel(data['url'], self.download_path, "Meilleure", data['date_after'])
                    
                    # Mise à jour date check
                    data['last_checked'] = time.time()
                    self.save_tracking()
                except Exception as e:
                    print(f"Erreur tracking {data['url']}: {e}")
                    
        self.after(0, lambda: self.auto_status_label.configure(text="En attente (Arrière-plan)...", text_color="gray"))

    # --- MINIMIZE TO TRAY ---
    def hide_window(self):
        # Si pystray n'est pas dispo, on quitte simplement
        if not pystray:
            self.is_running = False
            self.quit()
            return
            
        self.withdraw() # Cache la fenêtre
        image = Image.open("icon_download.png")
        menu = pystray.Menu(
            pystray.MenuItem('Ouvrir Video Pro', self.show_window),
            pystray.MenuItem('Quitter', self.quit_window)
        )
        self.tray_icon = pystray.Icon("name", image, "Video Downloader Pro", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self, icon, item):
        self.tray_icon.stop()
        self.after(0, self.deiconify)

    def quit_window(self, icon, item):
        self.is_running = False
        self.tray_icon.stop()
        self.quit()

    # --- HELPERS EXISTANTS ---
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f).get("download_path", os.path.join(os.path.expanduser("~"), "Downloads"))
            except: pass
        return os.path.join(os.path.expanduser("~"), "Downloads")
        
    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"download_path": self.download_path}, f)

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_path)
        if folder:
            self.download_path = folder
            display_path = self.download_path
            if len(display_path) > 40: display_path = "..." + display_path[-37:]
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
                    self.status_label.configure(text=f"Téléchargement en cours... {percent*100:.1f}%")
            except Exception: pass
        elif d['status'] == 'finished':
            self.progress_bar.set(1.0)
            self.status_label.configure(text="Téléchargement terminé avec succès ! 🎉", text_color="#107C10")
            self.download_button.configure(state="normal")
            
    def start_download(self):
        url = self.url_var.get().strip()
        if not url: return
        self.download_button.configure(state="disabled")
        self.progress_bar.pack(pady=10)
        self.status_label.configure(text="Préparation du téléchargement...", text_color="gray")
        self.progress_bar.set(0)
        threading.Thread(target=self.run_download_thread, args=(url, self.quality_var.get())).start()
        
    def run_download_thread(self, url, quality):
        try:
            download_video(url, self.download_path, quality, self.progress_hook)
        except Exception as e:
            self.status_label.configure(text=f"Erreur : {str(e)[:50]}...", text_color="#D13438")
            self.download_button.configure(state="normal")

if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.mainloop()
