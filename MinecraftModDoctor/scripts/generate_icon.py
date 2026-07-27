"""Uygulama simgesi oluşturucu."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
ICON_PATH = ASSETS_DIR / "icon.ico"
PNG_PATH = ASSETS_DIR / "icon.png"


def create_icon() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Minecraft yeşil arka plan (yuvarlak köşeli kare)
    margin = 16
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=40,
        fill=(26, 26, 26, 255),
        outline=(85, 170, 51, 255),
        width=6,
    )

    # Yeşil artı (mod doctor simgesi - tıbbi artı + kazma)
    center = size // 2
    green = (85, 170, 51, 255)

    # Artı
    bar_width = 28
    bar_length = 80
    draw.rectangle(
        [center - bar_width // 2, center - bar_length // 2, center + bar_width // 2, center + bar_length // 2],
        fill=green,
    )
    draw.rectangle(
        [center - bar_length // 2, center - bar_width // 2, center + bar_length // 2, center + bar_width // 2],
        fill=green,
    )

    # Kazma sapı (sol alt)
    draw.line([(70, 190), (110, 150)], fill=(139, 90, 43, 255), width=8)
    # Kazma başı
    draw.polygon([(105, 145), (130, 120), (145, 135), (120, 160)], fill=(180, 180, 180, 255))

    # PNG kaydet
    img.save(PNG_PATH, "PNG")

    # ICO kaydet (çoklu boyut) — 256 için ICO formatında 0 kullanılır
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = [img.resize(s, Image.Resampling.LANCZOS) for s, _ in sizes]

    def save_ico(path: Path, images: list[Image.Image], size_list: list[tuple[int, int]]) -> None:
        import struct
        png_data_list = []
        for im in images:
            from io import BytesIO
            buf = BytesIO()
            im.save(buf, format="PNG")
            png_data_list.append(buf.getvalue())

        count = len(images)
        header = struct.pack("<HHH", 0, 1, count)
        entries = b""
        offset = 6 + 16 * count
        for i, (w, h) in enumerate(size_list):
            bw = 0 if w >= 256 else w
            bh = 0 if h >= 256 else h
            entries += struct.pack("<BBBBHHII", bw, bh, 0, 0, 1, 32, len(png_data_list[i]), offset)
            offset += len(png_data_list[i])
        with open(path, "wb") as f:
            f.write(header + entries)
            for data in png_data_list:
                f.write(data)

    save_ico(ICON_PATH, icons, sizes)

    print(f"Simge olusturuldu: {ICON_PATH}")


if __name__ == "__main__":
    create_icon()
