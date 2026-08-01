import yt_dlp
import os

def download_video(url, output_path, quality_str, progress_hook=None):
    """
    Télécharge une vidéo depuis l'URL donnée de manière 100% Plug-and-Play.
    Utilise yt-dlp par défaut (TikTok, etc.), avec repli sur pytubefix pour YouTube si bloqué.
    """
    
    # Configuration des options pour yt-dlp
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'noplaylist': True,
        # Ruse : Se faire passer pour un client mobile ou TV pour éviter la détection de bot
        'extractor_args': {'youtube': ['player_client=ios,android,web']},
    }
    
    # Intégration automatique de FFmpeg pour la fusion Haute Définition
    try:
        import imageio_ffmpeg
        ydl_opts['ffmpeg_location'] = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
    
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

    try:
        # Lancement du téléchargement avec yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
    except Exception as e:
        error_msg = str(e).lower()
        # Si yt-dlp échoue sur YouTube à cause d'un blocage de bot ou d'IP (429), on bascule sur Pytubefix
        if "youtube" in url.lower() and ("429" in error_msg or "bot" in error_msg or "sign in" in error_msg or "decrypt" in error_msg):
            print("Blocage YouTube détecté. Bascule silencieuse vers Pytubefix...")
            try:
                from pytubefix import YouTube
                from pytubefix.cli import on_progress
                
                def pytube_progress(stream, chunk, bytes_remaining):
                    if progress_hook:
                        total = stream.filesize
                        downloaded = total - bytes_remaining
                        progress_hook({
                            'status': 'downloading',
                            'downloaded_bytes': downloaded,
                            'total_bytes': total
                        })
                        
                yt = YouTube(url, on_progress_callback=pytube_progress)
                
                if progress_hook:
                    # Initialisation visuelle pour montrer que ça démarre
                    progress_hook({'status': 'downloading', 'downloaded_bytes': 0, 'total_bytes': 100})
                
                if quality_str == "Audio seulement":
                    stream = yt.streams.get_audio_only()
                else:
                    stream = yt.streams.get_highest_resolution()
                    
                stream.download(output_path=output_path)
                
                if progress_hook:
                    progress_hook({'status': 'finished'})
            except Exception as e2:
                raise Exception(f"Les deux moteurs de téléchargement ont échoué. Détail: {str(e2)}")
        else:
            raise e

if __name__ == "__main__":
    pass
