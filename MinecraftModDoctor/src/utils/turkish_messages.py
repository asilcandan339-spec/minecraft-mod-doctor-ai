"""Türkçe hata mesajları ve açıklamalar."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ErrorExplanation:
    """Hata açıklaması."""

    original: str
    title: str
    explanation: str
    fix_steps: list[str]
    severity: str  # critical, error, warning, info


# Bilinen hata kalıpları ve Türkçe açıklamaları
ERROR_PATTERNS: list[tuple[str, str, str, list[str], str]] = [
    (
        r"java\.lang\.OutOfMemoryError",
        "Bellek Yetersiz (OutOfMemoryError)",
        "Minecraft yeterli RAM alanı bulamadı. Modlar ve kaynak paketleri çok fazla bellek tüketiyor olabilir.",
        [
            "Launcher ayarlarından JVM argümanlarına -Xmx4G veya -Xmx6G ekleyin (RAM'inize göre).",
            "Gereksiz modları devre dışı bırakın.",
            "Shader ve yüksek çözünürlüklü kaynak paketlerini kaldırın.",
            "Arka planda çalışan programları kapatın.",
        ],
        "critical",
    ),
    (
        r"ModResolutionException|mod.*failed to load|Could not find required mod",
        "Mod Yükleme Hatası",
        "Bir veya daha fazla mod yüklenemedi. Eksik bağımlılık veya uyumsuz mod sürümü olabilir.",
        [
            "Hata mesajında belirtilen eksik modu indirin.",
            "Mod sürümlerinin Minecraft ve loader sürümünüzle uyumlu olduğundan emin olun.",
            "Mod Doctor ile bağımlılık analizi yapın.",
        ],
        "critical",
    ),
    (
        r"IncompatibleClassChangeError|Mixin apply failed|Mixin transformation",
        "Mixin Uyumsuzluk Hatası",
        "Modlar arasında kod seviyesinde çakışma var. Genellikle aynı işlevi yapan modlar birlikte kullanıldığında oluşur.",
        [
            "OptiFine + Sodium/Iris gibi çakışan mod çiftlerinden birini kaldırın.",
            "Modları tek tek devre dışı bırakarak sorunlu modu bulun.",
            "Mod sürümlerini güncelleyin.",
        ],
        "critical",
    ),
    (
        r"NoClassDefFoundError|ClassNotFoundException",
        "Sınıf Bulunamadı Hatası",
        "Bir mod, ihtiyaç duyduğu kütüphane veya başka bir modu bulamıyor.",
        [
            "Eksik bağımlılık modunu indirip mods klasörüne ekleyin.",
            "Fabric API veya Forge gibi temel kütüphanelerin yüklü olduğundan emin olun.",
            "Mod sürümünün doğru loader için olduğunu kontrol edin.",
        ],
        "error",
    ),
    (
        r"java\.lang\.UnsupportedClassVersionError",
        "Java Sürüm Uyumsuzluğu",
        "Mod veya Minecraft, mevcut Java sürümünüzle uyumlu değil. Daha yeni veya daha eski Java gerekebilir.",
        [
            "Minecraft 1.20.5+ için Java 21, 1.18-1.20.4 için Java 17, eski sürümler için Java 8 kullanın.",
            "Launcher'dan doğru Java sürümünü seçin.",
            "Adoptium'dan uygun Java sürümünü indirin: https://adoptium.net",
        ],
        "critical",
    ),
    (
        r"Failed to load mod|error loading mod",
        "Mod Yükleme Başarısız",
        "Bir mod dosyası yüklenirken hata oluştu. Bozuk JAR veya yanlış sürüm olabilir.",
        [
            "Modu resmi kaynaktan yeniden indirin.",
            "mods.toml veya fabric.mod.json dosyasının doğru olduğunu kontrol edin.",
            "Mod Doctor ile JAR bütünlük kontrolü yapın.",
        ],
        "error",
    ),
    (
        r"Duplicate mods found|duplicate mod",
        "Yinelenen Mod",
        "Aynı modun birden fazla kopyası mods klasöründe bulunuyor.",
        [
            "mods klasöründe aynı modun farklı sürümlerini bulun.",
            "Eski sürümü 'Disabled Mods' klasörüne taşıyın.",
            "Sadece en güncel sürümü bırakın.",
        ],
        "warning",
    ),
    (
        r"OpenGL|GLFW|graphics driver|GPU",
        "Ekran Kartı / OpenGL Hatası",
        "Grafik sürücüsü veya OpenGL ile ilgili bir sorun var. Shader veya render modları etkilenebilir.",
        [
            "Ekran kartı sürücünüzü güncelleyin (NVIDIA/AMD/Intel).",
            "Shader'ı devre dışı bırakıp tekrar deneyin.",
            "Sodium/Iris yerine vanilla render ile test edin.",
        ],
        "error",
    ),
    (
        r"Connection refused|timed out|Unknown host",
        "Bağlantı Hatası",
        "Sunucuya veya internete bağlanılamıyor.",
        [
            "İnternet bağlantınızı kontrol edin.",
            "Sunucu adresinin doğru olduğundan emin olun.",
            "Firewall veya antivirüs Minecraft'ı engelliyor olabilir.",
        ],
        "warning",
    ),
    (
        r"Ticking entity|Ticking block entity|Exception ticking world",
        "Dünya İşleme Hatası",
        "Oyun dünyası işlenirken bir entity veya blok hatası oluştu. Genellikle bozuk bir mod veya chunk kaynaklıdır.",
        [
            "Son eklenen modu kaldırın.",
            "Bozuk chunk'ı MCEdit veya benzeri araçlarla düzeltin.",
            "Yedekten geri yükleyin.",
        ],
        "critical",
    ),
    (
        r"Registry.*already registered|Duplicate registry",
        "Kayıt Çakışması",
        "İki mod aynı blok, item veya entity'yi kaydetmeye çalışıyor.",
        [
            "Çakışan modları tespit edin ve birini kaldırın.",
            "Mod yapılandırma dosyalarında ID çakışması olup olmadığını kontrol edin.",
        ],
        "error",
    ),
    (
        r"Fabric Loader|fabric-loader",
        "Fabric Loader Sorunu",
        "Fabric Loader ile ilgili bir sorun tespit edildi.",
        [
            "Fabric Loader'ı resmi siteden güncelleyin: https://fabricmc.net",
            "Fabric API'nin yüklü ve güncel olduğundan emin olun.",
        ],
        "error",
    ),
    (
        r"Forge Mod Loader|net\.minecraftforge",
        "Forge Loader Sorunu",
        "Forge mod yükleyici ile ilgili bir sorun var.",
        [
            "Forge sürümünüzün Minecraft sürümüyle eşleştiğinden emin olun.",
            "Forge'u resmi siteden yeniden kurun: https://files.minecraftforge.net",
        ],
        "error",
    ),
    (
        r"NeoForge|net\.neoforged",
        "NeoForge Loader Sorunu",
        "NeoForge mod yükleyici ile ilgili bir sorun var.",
        [
            "NeoForge sürümünü güncelleyin: https://neoforged.net",
            "Eski Forge modlarının NeoForge ile uyumlu olmayabileceğini unutmayın.",
        ],
        "error",
    ),
    (
        r"FileNotFoundException.*mods",
        "Mod Dosyası Bulunamadı",
        "Bir mod dosyası eksik veya taşınmış.",
        [
            "mods klasörünü kontrol edin.",
            "Modu yeniden indirin.",
        ],
        "warning",
    ),
    (
        r"Invalid UUID|UUID",
        "UUID Hatası",
        "Oyuncu veya entity UUID'si geçersiz. Cracked launcher veya mod uyumsuzluğu olabilir.",
        [
            "Resmi launcher kullanmayı deneyin.",
            "Online fix modlarını kontrol edin.",
        ],
        "warning",
    ),
]


def explain_error(text: str) -> ErrorExplanation | None:
    """Metindeki hatayı Türkçe açıklar."""
    for pattern, title, explanation, fix_steps, severity in ERROR_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return ErrorExplanation(
                original=text[:500],
                title=title,
                explanation=explanation,
                fix_steps=fix_steps,
                severity=severity,
            )
    return None


def explain_generic_exception(line: str) -> ErrorExplanation:
    """Bilinmeyen hatalar için genel açıklama."""
    exception_match = re.search(r"(\w+(?:\.\w+)*Exception|\w+Error):\s*(.*)", line)
    if exception_match:
        exc_type = exception_match.group(1).split(".")[-1]
        msg = exception_match.group(2).strip()
        return ErrorExplanation(
            original=line[:500],
            title=f"Java Hatası: {exc_type}",
            explanation=(
                f"Oyun sırasında bir {exc_type} hatası oluştu. "
                f"Mesaj: {msg if msg else 'Detay belirtilmemiş'}. "
                "Bu genellikle bir mod uyumsuzluğu, eksik bağımlılık veya bozuk dosyadan kaynaklanır."
            ),
            fix_steps=[
                "Son eklediğiniz modu kaldırıp tekrar deneyin.",
                "Mod Doctor ile tam tarama yapın.",
                "latest.log dosyasının tamamını AI asistanına sorun.",
                "Modları güncelleyin veya yedekten geri yükleyin.",
            ],
            severity="error",
        )
    return ErrorExplanation(
        original=line[:500],
        title="Bilinmeyen Hata",
        explanation="Log dosyasında bir hata tespit edildi ancak otomatik sınıflandırılamadı.",
        fix_steps=[
            "Tam log dosyasını inceleyin.",
            "Mod Doctor AI asistanına sorun.",
        ],
        severity="warning",
    )


SEVERITY_LABELS = {
    "critical": "Kritik",
    "error": "Hata",
    "warning": "Uyarı",
    "info": "Bilgi",
}

LOADER_LABELS = {
    "fabric": "Fabric",
    "forge": "Forge",
    "neoforge": "NeoForge",
    "quilt": "Quilt",
    "unknown": "Bilinmiyor",
}
