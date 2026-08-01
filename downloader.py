import yt_dlp
import os

def download_video(url, output_path, quality_str, progress_hook=None):
    """
    Télécharge une vidéo depuis l'URL donnée de manière 100% Plug-and-Play.
    Utilise yt-dlp par défaut (TikTok, etc.), avec repli sur pytubefix pour YouTube si bloqué.
    """
    
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'extractor_args': {'youtube': ['player_client=ios,android,web']},
    }
    
    try:
        import imageio_ffmpeg
        ydl_opts['ffmpeg_location'] = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
    
    if progress_hook:
        ydl_opts['progress_hooks'] = [progress_hook]

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
    else: 
        ydl_opts['format'] = 'bestvideo+bestaudio/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        error_msg = str(e).lower()
        if "youtube" in url.lower() and ("429" in error_msg or "bot" in error_msg or "sign in" in error_msg or "decrypt" in error_msg):
            print("Blocage YouTube détecté. Bascule silencieuse vers Pytubefix...")
            try:
                from pytubefix import YouTube
                
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

def download_channel(url, output_path, quality_str, date_after=None, progress_hook=None):
    """
    Télécharge une chaîne entière, avec historique (archive.txt) pour ignorer les vidéos déjà téléchargées.
    """
    
    # On crée un sous-dossier par chaîne automatiquement
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(uploader)s', '%(title)s.%(ext)s'),
        'noplaylist': False, # Autoriser le téléchargement de chaîne
        'extractor_args': {'youtube': ['player_client=ios,android,web']},
        'download_archive': os.path.join(output_path, 'archive.txt'), # Fichier de mémorisation !
        'ignoreerrors': True, # Ignorer si une vidéo crashe et passer à la suivante
    }
    
    if date_after:
        # yt-dlp attend le format YYYYMMDD
        clean_date = date_after.replace("-", "").replace("/", "")
        ydl_opts['daterange'] = yt_dlp.utils.DateRange(start=clean_date)
        
    try:
        import imageio_ffmpeg
        ydl_opts['ffmpeg_location'] = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
        
    if progress_hook:
        ydl_opts['progress_hooks'] = [progress_hook]

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
    else: 
        ydl_opts['format'] = 'bestvideo+bestaudio/best'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

if __name__ == "__main__":
    pass
