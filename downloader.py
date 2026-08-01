import yt_dlp
import os
import re

class YTDLLogger:
    def __init__(self, stats_hook, url):
        self.stats_hook = stats_hook
        self.url = url
        self.total = 0
        self.downloaded_count = 0
        
    def debug(self, msg):
        if "Downloading " in msg and "items of " in msg:
            match = re.search(r'Downloading (\d+) items', msg)
            if match:
                self.total = int(match.group(1))
                self.update("Vérification...")
        elif "has already been recorded in the archive" in msg:
            self.downloaded_count += 1
            self.update("Vérification...")
            
    def update(self, status):
        if self.stats_hook:
            self.stats_hook(self.url, {
                'status': status,
                'total': self.total,
                'downloaded': self.downloaded_count
            })
            
    def warning(self, msg):
        pass
        
    def error(self, msg):
        pass

def download_video(url, output_path, quality_str, progress_hook=None):
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

def download_channel(url, output_path, quality_str, date_after=None, progress_hook=None, stats_hook=None):
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(uploader)s', '%(title)s.%(ext)s'),
        'noplaylist': False,
        'extractor_args': {'youtube': ['player_client=ios,android,web']},
        'download_archive': os.path.join(output_path, 'archive.txt'),
        'ignoreerrors': True,
    }
    
    logger = YTDLLogger(stats_hook, url)
    ydl_opts['logger'] = logger
    
    if date_after:
        clean_date = date_after.replace("-", "").replace("/", "")
        ydl_opts['daterange'] = yt_dlp.utils.DateRange(start=clean_date)
        
    try:
        import imageio_ffmpeg
        ydl_opts['ffmpeg_location'] = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
        
    def internal_hook(d):
        if d['status'] == 'finished':
            logger.downloaded_count += 1
            logger.update("Téléchargement en cours...")
        elif d['status'] == 'downloading':
            logger.update(f"Téléchargement... {d.get('_percent_str', '').strip()}")
            
        if progress_hook:
            progress_hook(d)

    ydl_opts['progress_hooks'] = [internal_hook]

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
        
    # Fin
    logger.update("En attente")

if __name__ == "__main__":
    pass
