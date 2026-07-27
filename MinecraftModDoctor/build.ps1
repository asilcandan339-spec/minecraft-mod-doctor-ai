# Minecraft Mod Doctor AI - PowerShell Build Script
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "============================================" -ForegroundColor Green
Write-Host " Minecraft Mod Doctor AI - Build Script" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

Set-Location $PSScriptRoot

# Sanal ortam
if (-not (Test-Path "venv")) {
    Write-Host "[1/4] Sanal ortam olusturuluyor..." -ForegroundColor Yellow
    python -m venv venv
} else {
    Write-Host "[1/4] Sanal ortam mevcut." -ForegroundColor Yellow
}

& ".\venv\Scripts\Activate.ps1"

Write-Host "[2/4] Bagimliliklar yukleniyor..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host "[3/4] Simge olusturuluyor..." -ForegroundColor Yellow
python scripts\generate_icon.py

Write-Host "[4/4] PyInstaller ile derleniyor..." -ForegroundColor Yellow
pyinstaller build.spec --noconfirm

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " Derleme tamamlandi!" -ForegroundColor Green
Write-Host " EXE: dist\MinecraftModDoctorAI.exe" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Green
