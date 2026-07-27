# Minecraft Mod Doctor AI

Minecraft modlarını otomatik analiz eden, crash ve uyumsuzluk sorunlarını Türkçe açıklayan, Windows masaüstü uygulaması.

## Özellikler

- **Otomatik Kurulum Tespiti**: Resmi Launcher, TLauncher, SKLauncher, Prism Launcher, CurseForge, MultiMC, GDLauncher ve özel `.minecraft` klasörleri
- **Kapsamlı Tarama**: Modlar, loglar, crash-report, config, resourcepack, shaderpack, sürümler, kütüphaneler
- **Mod Analizi**: Fabric, Forge, NeoForge, Quilt desteği; bağımlılık, bozuk JAR, yinelenen mod tespiti
- **Log Analizi**: `latest.log`, `debug.log`, crash-report — her hata basit Türkçe ile açıklanır
- **AI Asistan**: Mod sorunları, FPS, crash ve uyumluluk hakkında Türkçe soru-cevap
- **Otomatik Düzeltme**: Yedek alır, uyumsuz modları `Disabled Mods` klasörüne taşır, bağımlılık indirir
- **Performans Analizi**: CPU, RAM, tahmini FPS, ağır mod tespiti
- **Sağlık Skoru**: Uyumluluk %, Çökme Riski %, Performans %
- **PDF Raporu**: Detaylı analiz raporu oluşturma
- **Yedekleme**: Mod ve config yedekleme / geri yükleme

## Gereksinimler

- Windows 10/11
- Python 3.13
- İnternet bağlantısı (bağımlılık indirme ve Modrinth API için)

## Kurulum

```bash
# Depoyu klonlayın veya indirin
cd MinecraftModDoctor

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Simge oluşturun (isteğe bağlı)
python scripts/generate_icon.py

# Uygulamayı çalıştırın
python main.py
```

## EXE Derleme

### Batch (CMD)
```batch
build.bat
```

### PowerShell
```powershell
.\build.ps1
```

### Manuel
```bash
pip install -r requirements.txt
python scripts/generate_icon.py
pyinstaller build.spec
```

Derlenmiş EXE: `dist/MinecraftModDoctorAI.exe`

## Installer Oluşturma

Inno Setup 6 yüklü olmalıdır:

```bash
# Önce EXE derleyin
.\build.ps1

# Installer oluşturun
iscc installer.iss
```

Installer çıktısı: `installer_output/MinecraftModDoctorAI_Setup.exe`

## Kullanım

1. Uygulamayı başlatın
2. Tespit edilen Minecraft kurulumunu seçin
3. **Minecraft'ı Tara** butonuna tıklayın
4. Sonuçları inceleyin, sağlık skoruna bakın
5. **Otomatik Düzelt** ile sorunları giderin
6. **AI'ye Sor** ile sorularınızı sorun
7. **PDF Raporu Oluştur** ile rapor alın

## AI API (İsteğe Bağlı)

Harici LLM API kullanmak için ortam değişkenleri:

```bash
set MODDOCTOR_AI_URL=https://api.openai.com/v1/chat/completions
set MODDOCTOR_AI_KEY=sk-...
```

API yapılandırılmazsa yerleşik bilgi tabanlı asistan kullanılır.

## Proje Yapısı

```
MinecraftModDoctor/
├── main.py                 # Giriş noktası
├── build.spec              # PyInstaller spec
├── build.bat / build.ps1   # Derleme scriptleri
├── installer.iss           # Inno Setup installer
├── requirements.txt
├── assets/                 # Simge ve görseller
├── scripts/                # Yardımcı scriptler
└── src/
    ├── app.py              # Uygulama başlatıcı
    ├── config.py           # Yapılandırma
    ├── ai/                 # AI asistan
    ├── core/               # Analiz motorları
    ├── database/           # SQLite
    ├── reports/            # PDF rapor
    ├── ui/                 # CustomTkinter arayüz
    └── utils/              # Yardımcı araçlar
```

## Veri Konumu

Uygulama verileri:
```
%LOCALAPPDATA%\MinecraftModDoctor\
├── moddoctor.db      # Tarama geçmişi
├── backups/          # Yedekler
├── reports/          # PDF raporlar
└── cache/            # Önbellek
```

## Lisans

MIT License
