@echo off
echo Compilation du Video Downloader en cours...
echo Cela peut prendre quelques minutes.

pyinstaller --noconfirm --onedir --windowed --name "VideoDownloader"  "gui.py"

echo Termine ! Le fichier executable se trouve dans le dossier "dist\VideoDownloader".
pause
