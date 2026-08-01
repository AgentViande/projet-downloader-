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

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "config.json"
TRACKING_FILE = "tracking.json"

class VideoDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Video Downloader Pro")
        self.geometry("1100x750")
        self.minsize(900, 500)
        
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
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
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
            self.icon_yt = ctk.CTkImage(Image.open("icon_youtube.png"), size=(24, 24))
            self.icon_tk = ctk.CTkImage(Image.open("icon_tiktok.png"), size=(24, 24))
            self.icon_web = ctk.CTkImage(Image.open("icon_web.png"), size=(24, 24))
        except Exception:
            self.icon_download, self.icon_logo, self.icon_auto = None, None, None
            self.icon_yt, self.icon_tk, self.icon_web = None, None, None

        self.logo_label = ctk.CTkLabel(
            self.top_sidebar_frame, text=" Video Pro", image=self.icon_logo,
            compound="left", font=ctk.CTkFont(family="Segoe UI Variable Display", size=18, weight="bold")
        )
        self.logo_label.pack(side="left", padx=(10, 10))
        
        self.tab_download_btn = ctk.CTkButton(
            self.sidebar_frame, text=" Télécharger", image=self.icon_download,
            compound="left", anchor="w", fg_color=("gray80", "gray20"),
            text_color=("black", "white"), hover_color=("gray70", "gray30"),
            height=45, width=180, font=self.main_font,
            command=self.show_download_tab
        )
        self.tab_download_btn.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.tab_auto_btn = ctk.CTkButton(
            self.sidebar_frame, text=" Suivi Auto", image=self.icon_auto,
            compound="left", anchor="w", fg_color="transparent",
            text_color=("black", "white"), hover_color=("gray70", "gray30"),
            height=45, width=180, font=self.main_font,
            command=self.show_auto_tab
        )
        self.tab_auto_btn.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        self.main_view = ctk.CTkFrame(self, fg_color="transparent")
        self.main_view.grid(row=0, column=1, sticky="nsew")
        
        self.tracking_ui_elements = {}
        
        self.setup_download_tab()
        self.setup_auto_tab()
        self.show_download_tab()
        
        self.is_running = True
        self.bg_thread = threading.Thread(target=self.background_worker, daemon=True)
        self.bg_thread.start()

    def show_download_tab(self):
        self.auto_container.pack_forget()
        self.download_container.pack(fill="both", expand=True)
        self.tab_download_btn.configure(fg_color=("gray80", "gray20"))
        self.tab_auto_btn.configure(fg_color="transparent")
        
    def show_auto_tab(self):
        self.download_container.pack_forget()
        self.auto_container.pack(fill="both", expand=True, padx=20, pady=20)
        self.tab_auto_btn.configure(fg_color=("gray80", "gray20"))
        self.tab_download_btn.configure(fg_color="transparent")

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
        
        # Center wrapper
        center_wrapper = ctk.CTkFrame(self.download_container, fg_color="transparent")
        center_wrapper.place(relx=0.5, rely=0.5, anchor="center")
        
        title_font = ctk.CTkFont(family="Segoe UI Variable Display", size=34, weight="bold")
        button_font = ctk.CTkFont(family="Segoe UI Variable Text", size=16, weight="bold")

        ctk.CTkLabel(center_wrapper, text="Télécharger une vidéo", font=title_font).pack(pady=(0, 40))

        self.url_var = tk.StringVar()
        ctk.CTkEntry(center_wrapper, width=550, height=50, corner_radius=10, font=self.main_font,
                     placeholder_text="Collez un lien YouTube, TikTok, Instagram...", textvariable=self.url_var).pack(pady=(0, 30))

        options_card = ctk.CTkFrame(center_wrapper, corner_radius=12, fg_color=("#f3f3f3", "#2b2b2b"), border_width=1, border_color=("#e5e5e5", "#333333"))
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
        
        ctk.CTkButton(f_frame, text="Modifier...", command=self.choose_folder, font=self.main_font, corner_radius=6,
                      width=100, fg_color="transparent", border_width=1, text_color=("black", "white"), hover_color=("#e5e5e5", "#444444")).pack(side="right", padx=10)

        self.download_button = ctk.CTkButton(center_wrapper, text="Télécharger", command=self.start_download, font=button_font, height=50, width=280, corner_radius=25)
        self.download_button.pack(pady=(10, 15))

        self.progress_bar = ctk.CTkProgressBar(center_wrapper, width=550, height=6)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10)
        self.progress_bar.pack_forget()
        
        self.status_label = ctk.CTkLabel(center_wrapper, text="", font=self.main_font, text_color="gray")
        self.status_label.pack()

    # --- SETUP ONGLET SUIVI AUTO ---
    def setup_auto_tab(self):
        self.auto_container = ctk.CTkFrame(self.main_view, fg_color="transparent")
        
        # TOP BAR
        top_bar = ctk.CTkFrame(self.auto_container, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 20))
        
        title_font = ctk.CTkFont(family="Segoe UI Variable Display", size=34, weight="bold")
        ctk.CTkLabel(top_bar, text="Suivi Automatique", font=title_font).pack(side="left")
        
        ctk.CTkButton(top_bar, text="+ Ajouter une chaîne", width=160, height=45, font=ctk.CTkFont(weight="bold"), 
                      corner_radius=22, command=self.open_add_tracking_popup).pack(side="right")
                      
        # HEADER DU TABLEAU
        header_frame = ctk.CTkFrame(self.auto_container, corner_radius=8, fg_color=("#f0f0f0", "#202020"))
        header_frame.pack(fill="x", pady=(0, 10), ipady=5)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Largeurs fixes pour l'alignement
        ctk.CTkLabel(header_frame, text="Site", font=ctk.CTkFont(weight="bold"), width=60).grid(row=0, column=0, padx=5)
        ctk.CTkLabel(header_frame, text="Lien", font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=1, sticky="w", padx=10)
        ctk.CTkLabel(header_frame, text="Qualité", font=ctk.CTkFont(weight="bold"), width=120).grid(row=0, column=2, padx=5)
        ctk.CTkLabel(header_frame, text="Paramètres", font=ctk.CTkFont(weight="bold"), width=140).grid(row=0, column=3, padx=5)
        ctk.CTkLabel(header_frame, text="Vidéos", font=ctk.CTkFont(weight="bold"), width=100).grid(row=0, column=4, padx=5)
        ctk.CTkLabel(header_frame, text="Statut", font=ctk.CTkFont(weight="bold"), width=160).grid(row=0, column=5, padx=5)
        ctk.CTkLabel(header_frame, text="", width=40).grid(row=0, column=6, padx=5) # Place pour bouton delete

        # TABLEAU (Contenu)
        self.channels_frame = ctk.CTkScrollableFrame(self.auto_container, fg_color="transparent")
        self.channels_frame.pack(fill="both", expand=True)
        
        # BOTTOM BAR
        bottom_frame = ctk.CTkFrame(self.auto_container, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(bottom_frame, text="Lancer la vérification forcée", command=self.force_check, corner_radius=20, fg_color="#107C10", hover_color="#0B5C0B").pack(side="right")
        
        self.refresh_tracking_list()

    def open_add_tracking_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Ajouter une chaîne au suivi")
        popup.geometry("520x450")
        popup.resizable(False, False)
        # Centrer sur l'application principale
        popup.transient(self)
        popup.grab_set()
        
        # Application du style Mica sur le popup si dispo
        if pywinstyles:
            try:
                pywinstyles.apply_style(popup, "mica")
                popup.configure(fg_color="transparent")
            except Exception:
                pass
                
        container = ctk.CTkFrame(popup, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(container, text="Nouvelle Chaîne", font=ctk.CTkFont(family="Segoe UI Variable Display", size=24, weight="bold")).pack(pady=(0, 20))
        
        url_var = tk.StringVar()
        ctk.CTkEntry(container, textvariable=url_var, placeholder_text="Lien de la chaîne", width=420, height=40).pack(pady=(0, 15))
        
        # Options frame
        opt_frame = ctk.CTkFrame(container, fg_color="transparent")
        opt_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(opt_frame, text="Qualité :").grid(row=0, column=0, sticky="w", pady=5)
        qual_var = ctk.StringVar(value="Meilleure")
        ctk.CTkOptionMenu(opt_frame, values=["Meilleure", "1080p", "720p", "480p", "Audio seulement"], variable=qual_var).grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        ctk.CTkLabel(opt_frame, text="Depuis le :").grid(row=1, column=0, sticky="w", pady=5)
        date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ctk.CTkEntry(opt_frame, textvariable=date_var, width=120).grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        ctk.CTkLabel(opt_frame, text="Intervalle (H) :").grid(row=2, column=0, sticky="w", pady=5)
        interval_var = tk.StringVar(value="6")
        ctk.CTkEntry(opt_frame, textvariable=interval_var, width=60).grid(row=2, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(opt_frame, text="Dossier :").grid(row=3, column=0, sticky="w", pady=5)
        folder_frame = ctk.CTkFrame(opt_frame, fg_color="transparent")
        folder_frame.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        
        selected_folder = tk.StringVar(value=self.download_path)
        
        def choose_custom_folder():
            f = filedialog.askdirectory(initialdir=selected_folder.get())
            if f:
                selected_folder.set(f)
                disp = f if len(f) <= 25 else "..." + f[-22:]
                lbl_path.configure(text=disp)
                
        disp = selected_folder.get()
        disp = disp if len(disp) <= 25 else "..." + disp[-22:]
        lbl_path = ctk.CTkLabel(folder_frame, text=disp, width=160, anchor="w", text_color="gray")
        lbl_path.pack(side="left")
        ctk.CTkButton(folder_frame, text="Parcourir...", width=80, command=choose_custom_folder).pack(side="left", padx=5)
        
        def save_action():
            url = url_var.get().strip()
            if not url: return
            self.tracking_data.append({
                "url": url,
                "quality": qual_var.get(),
                "date_after": date_var.get(),
                "interval": float(interval_var.get()),
                "custom_path": selected_folder.get(),
                "last_checked": 0,
                "stats_downloaded": 0,
                "stats_total": "?",
                "status": "En attente"
            })
            self.save_tracking()
            self.refresh_tracking_list()
            popup.destroy()
            
        ctk.CTkButton(container, text="Ajouter au suivi", command=save_action, height=45, corner_radius=20, font=ctk.CTkFont(weight="bold")).pack(pady=20, side="bottom")

    def get_site_icon(self, url):
        u = url.lower()
        if "youtube" in u or "youtu.be" in u: return self.icon_yt
        elif "tiktok" in u: return self.icon_tk
        return self.icon_web

    def load_tracking(self):
        if os.path.exists(TRACKING_FILE):
            try:
                with open(TRACKING_FILE, 'r') as f:
                    return json.load(f)
            except: pass
        return []

    def save_tracking(self):
        with open(TRACKING_FILE, 'w') as f:
            json.dump(self.tracking_data, f)
            
    def remove_tracking(self, index):
        if 0 <= index < len(self.tracking_data):
            del self.tracking_data[index]
            self.save_tracking()
            self.refresh_tracking_list()

    def refresh_tracking_list(self):
        for widget in self.channels_frame.winfo_children():
            widget.destroy()
        self.tracking_ui_elements.clear()
            
        for i, data in enumerate(self.tracking_data):
            f = ctk.CTkFrame(self.channels_frame, corner_radius=6, fg_color=("#ffffff", "#2b2b2b"), border_width=1, border_color=("#e5e5e5", "#333333"))
            f.pack(fill="x", pady=4, padx=2)
            f.grid_columnconfigure(1, weight=1)
            
            icon = self.get_site_icon(data['url'])
            ctk.CTkLabel(f, text="", image=icon, width=60).grid(row=0, column=0, padx=5, pady=8)
            
            url_short = data['url']
            if len(url_short) > 40: url_short = url_short[:40] + "..."
            ctk.CTkLabel(f, text=url_short, font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=1, sticky="w", padx=10)
            
            qual = data.get('quality', 'Meilleure')
            ctk.CTkLabel(f, text=qual, width=120).grid(row=0, column=2, padx=5)
            
            ctk.CTkLabel(f, text=f"{data['interval']}h | {data.get('date_after', 'All')}", text_color="gray", width=140).grid(row=0, column=3, padx=5)
            
            dl = data.get('stats_downloaded', 0)
            tot = data.get('stats_total', '?')
            lbl_stats = ctk.CTkLabel(f, text=f"{dl} / {tot}", font=ctk.CTkFont(weight="bold"), width=100)
            lbl_stats.grid(row=0, column=4, padx=5)
            
            status = data.get('status', 'En attente')
            status_frame = ctk.CTkFrame(f, fg_color="transparent")
            status_frame.grid(row=0, column=5, padx=5, sticky="we")
            
            lbl_status = ctk.CTkLabel(status_frame, text=status, text_color="gray", width=160, anchor="w")
            lbl_status.pack(anchor="w")
            
            prog_bar = ctk.CTkProgressBar(status_frame, width=150, height=5)
            prog_bar.set(0)
            if "Téléchargement..." in status:
                prog_bar.pack(anchor="w", pady=(2, 0))
            
            ctk.CTkButton(f, text="X", width=30, height=30, fg_color="#D13438", hover_color="#A80000", 
                          command=lambda idx=i: self.remove_tracking(idx)).grid(row=0, column=6, padx=10)
                          
            self.tracking_ui_elements[data['url']] = {
                'lbl_stats': lbl_stats,
                'lbl_status': lbl_status,
                'prog_bar': prog_bar,
                'data_ref': data
            }

    # --- UI UPDATE HOOK ---
    def auto_stats_hook(self, url, info):
        if url in self.tracking_ui_elements:
            ui = self.tracking_ui_elements[url]
            data = ui['data_ref']
            
            status = info.get('status', data.get('status'))
            tot = info.get('total', data.get('stats_total'))
            dl = info.get('downloaded', data.get('stats_downloaded'))
            percent = info.get('percent', None)
            
            data['status'] = status
            if tot != 0: data['stats_total'] = tot
            data['stats_downloaded'] = dl
            
            self.after(0, lambda u=url, t=tot, d=dl, s=status, p=percent: self._update_ui_row(u, t, d, s, p))

    def _update_ui_row(self, url, tot, dl, status, percent):
        if url in self.tracking_ui_elements:
            ui = self.tracking_ui_elements[url]
            if tot != 0:
                ui['lbl_stats'].configure(text=f"{dl} / {tot}")
            ui['lbl_status'].configure(text=status)
            
            prog = ui['prog_bar']
            if "Téléchargement..." in status and percent is not None:
                prog.pack(anchor="w", pady=(2, 0))
                prog.set(percent)
            elif "En attente" in status or "Initialisation" in status or "Vérification" in status:
                prog.pack_forget()
                
            if "En attente" in status:
                self.save_tracking()

    # --- BACKGROUND WORKER ---
    def force_check(self):
        threading.Thread(target=self.run_checks, args=(True,), daemon=True).start()

    def background_worker(self):
        while self.is_running:
            self.run_checks()
            time.sleep(60)

    def run_checks(self, force=False):
        now = time.time()
        for data in self.tracking_data:
            interval_seconds = data['interval'] * 3600
            if force or (now - data.get('last_checked', 0) > interval_seconds):
                try:
                    self.auto_stats_hook(data['url'], {'status': '🔍 Initialisation...'})
                    qual = data.get('quality', 'Meilleure')
                    out_path = data.get('custom_path', self.download_path)
                    download_channel(data['url'], out_path, qual, data['date_after'], stats_hook=self.auto_stats_hook)
                    data['last_checked'] = time.time()
                    self.auto_stats_hook(data['url'], {'status': '😴 En attente'})
                except Exception as e:
                    print(f"Erreur tracking {data['url']}: {e}")
                    self.auto_stats_hook(data['url'], {'status': 'Erreur'})

    # --- MINIMIZE TO TRAY ---
    def hide_window(self):
        if not pystray:
            self.is_running = False
            self.quit()
            return
            
        self.withdraw()
        image = Image.open("icon_download.png")
        menu = pystray.Menu(pystray.MenuItem('Ouvrir Video Pro', self.show_window), pystray.MenuItem('Quitter', self.quit_window))
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
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                dl = d.get('downloaded_bytes', 0)
                if total:
                    self.progress_bar.set(dl / total)
                    self.status_label.configure(text=f"Téléchargement en cours... {(dl/total)*100:.1f}%")
            except: pass
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
