import yt_dlp
import os

def download_video(url, output_path, quality_str, browser="Aucun", progress_hook=None):
    """
    Télécharge une vidéo depuis l'URL donnée avec yt_dlp.
    """
    
    # Configuration des options pour yt-dlp
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'noplaylist': True,
        # Ruse : Se faire passer pour un client mobile ou TV pour éviter la détection de bot
        'extractor_args': {'youtube': ['player_client=ios,android,web']},
    }

    if browser and browser != "Aucun":
        ydl_opts['cookiesfrombrowser'] = (browser.lower(),)
    
    # Si on a fourni une fonction pour la barre de progression, on l'ajoute
    if progress_hook:
        ydl_opts['progress_hooks'] = [progress_hook]

    # Paramétrage de la qualité
    if quality_str == "Audio seulement":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    elif quality_str == "1080p":
        ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
    elif quality_str == "720p":
        ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
    elif quality_str == "480p":
        ydl_opts['format'] = 'bestvideo[height<=480]+bestaudio/best[height<=480]/best'
    else: # "Meilleure" par défaut
        ydl_opts['format'] = 'bestvideo+bestaudio/best'

    # Lancement du téléchargement
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

if __name__ == "__main__":
    # Test simple (sans GUI)
    pass
