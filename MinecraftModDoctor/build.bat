@echo off
chcp 65001 >nul
echo ============================================
echo  Minecraft Mod Doctor AI - Build Script
echo ============================================
echo.

cd /d "%~dp0"

echo [1/4] Sanal ortam kontrolu...
if not exist "venv" (
    echo Sanal ortam olusturuluyor...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo [2/4] Bagimliliklar yukleniyor...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [3/4] Simge olusturuluyor...
python scripts\generate_icon.py

echo [4/4] PyInstaller ile derleniyor...
pyinstaller build.spec --noconfirm

echo.
echo ============================================
echo  Derleme tamamlandi!
echo  EXE: dist\MinecraftModDoctorAI.exe
echo ============================================
pause
