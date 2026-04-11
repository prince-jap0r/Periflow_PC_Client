from __future__ import annotations

from pathlib import Path
from shutil import copyfile

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = PROJECT_ROOT / "Assets"
BUILD_ASSETS_DIR = PROJECT_ROOT / "build_assets"
SOURCE_LOGO = ASSETS_DIR / "playstore.png"
TARGET_PNG = BUILD_ASSETS_DIR / "periflow_logo.png"
TARGET_ICO = BUILD_ASSETS_DIR / "periflow.ico"


def main() -> None:
    BUILD_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    copyfile(SOURCE_LOGO, TARGET_PNG)

    image = Image.open(SOURCE_LOGO).convert("RGBA")
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    image.save(TARGET_ICO, sizes=sizes)
    print(f"Prepared {TARGET_PNG}")
    print(f"Prepared {TARGET_ICO}")


if __name__ == "__main__":
    main()
