"""Build a local, installable Anki add-on archive."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parent
output = root / "dist" / "Tap to Flip.ankiaddon"
output.parent.mkdir(exist_ok=True)
with ZipFile(output, "w", ZIP_DEFLATED) as archive:
    for name in ("__init__.py", "config.json", "manifest.json"):
        archive.write(root / "addon" / name, name)
print(output)
