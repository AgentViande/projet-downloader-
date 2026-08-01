import yt_dlp
import os
import re

class DownloadCancelled(BaseException): pass
class DownloadPaused(BaseException): pass

CANCELED_URLS = set()
PAUSED_URLS = set()

def cancel_download(url):
    CANCELED_URLS.add(url)
    if url in PAUSED_URLS:
        PAUSED_URLS.remove(url)

def pause_download(url):
    PAUSED_URLS.add(url)

def resume_download(url):
    if url in PAUSED_URLS:
        PAUSED_URLS.remove(url)
    if url in CANCELED_URLS:
        CANCELED_URLS.remove(url)

def _check_abort(url):
    if url in CANCELED_URLS:
        raise DownloadCancelled("Téléchargement annulé par l'utilisateur.")
    if url in PAUSED_URLS:
        raise DownloadPaused("Téléchargement mis en pause.")

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
            
    def warning(self, msg): pass
    def error(self, msg): pass

def download_video(url, output_path, quality_str, progress_hook=None, global_hook=None):
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
    
    def internal_hook(d):
        _check_abort(url)
            
        if 'info_dict' not in d: d['info_dict'] = {}
        d['info_dict']['_custom_quality'] = quality_str
        d['info_dict']['_custom_path'] = output_path
        
        if global_hook:
            global_hook(d)
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

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except DownloadCancelled:
        raise
    except DownloadPaused:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "youtube" in url.lower() and ("429" in error_msg or "bot" in error_msg or "sign in" in error_msg or "decrypt" in error_msg):
            print("Blocage YouTube détecté. Bascule vers Pytubefix...")
            try:
                from pytubefix import YouTube
                
                def pytube_progress(stream, chunk, bytes_remaining):
                    _check_abort(url)
                    total = stream.filesize
                    downloaded = total - bytes_remaining
                    d = {
                        'status': 'downloading',
                        'downloaded_bytes': downloaded,
                        'total_bytes': total,
                        'info_dict': {
                            'title': yt.title,
                            'uploader': yt.author,
                            'thumbnail': yt.thumbnail_url,
                            'webpage_url': url,
                            '_custom_quality': quality_str,
                            '_custom_path': output_path
                        }
                    }
                    if global_hook: global_hook(d)
                    if progress_hook: progress_hook(d)
                        
                yt = YouTube(url, on_progress_callback=pytube_progress)
                
                init_d = {
                    'status': 'downloading', 
                    'downloaded_bytes': 0, 
                    'total_bytes': 100,
                    'info_dict': {
                        'title': yt.title,
                        'uploader': yt.author,
                        'thumbnail': yt.thumbnail_url,
                        'webpage_url': url,
                        '_custom_quality': quality_str,
                        '_custom_path': output_path
                    }
                }
                if global_hook: global_hook(init_d)
                if progress_hook: progress_hook(init_d)
                
                if quality_str == "Audio seulement":
                    stream = yt.streams.get_audio_only()
                else:
                    stream = yt.streams.get_highest_resolution()
                    
                stream.download(output_path=output_path)
                
                fin_d = {
                    'status': 'finished',
                    'info_dict': {
                        'title': yt.title,
                        'uploader': yt.author,
                        'thumbnail': yt.thumbnail_url,
                        'webpage_url': url,
                        '_custom_quality': quality_str,
                        '_custom_path': output_path
                    }
                }
                if global_hook: global_hook(fin_d)
                if progress_hook: progress_hook(fin_d)
            except DownloadCancelled:
                raise
            except DownloadPaused:
                raise
            except Exception as e2:
                raise Exception(f"Les deux moteurs ont échoué. Détail: {str(e2)}")
        else:
            raise e

def download_channel(url, output_path, quality_str, date_after=None, progress_hook=None, stats_hook=None, global_hook=None):
    def abort_filter(info_dict):
        # We must check the specific VIDEO URL extracted from the playlist, but also the CHANNEL URL if the user canceled the channel.
        _check_abort(url) # channel url
        video_url = info_dict.get('webpage_url', '')
        if video_url: _check_abort(video_url)
        return None

    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(uploader)s', '%(title)s.%(ext)s'),
        'noplaylist': False,
        'extractor_args': {'youtube': ['player_client=ios,android,web']},
        'download_archive': os.path.join(output_path, 'archive.txt'),
        'ignoreerrors': True,
        'match_filter': abort_filter
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
        video_url = d.get('info_dict', {}).get('webpage_url', '')
        _check_abort(url)
        if video_url: _check_abort(video_url)
            
        if 'info_dict' not in d: d['info_dict'] = {}
        d['info_dict']['_custom_quality'] = quality_str
        d['info_dict']['_custom_path'] = output_path
            
        if d['status'] == 'finished':
            logger.downloaded_count += 1
            logger.update("Téléchargement...")
        elif d['status'] == 'downloading':
            percent_float = 0
            try:
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                dl = d.get('downloaded_bytes', 0)
                if total:
                    percent_float = dl / total
            except:
                pass
                
            if stats_hook:
                stats_hook(url, {
                    'status': f"Téléchargement... {d.get('_percent_str', '').strip()}",
                    'total': logger.total,
                    'downloaded': logger.downloaded_count,
                    'percent': percent_float
                })
                
        if global_hook:
            global_hook(d)
            
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

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except DownloadCancelled:
        pass
    except DownloadPaused:
        pass
        
    logger.update("En attente")

if __name__ == "__main__":
    pass
