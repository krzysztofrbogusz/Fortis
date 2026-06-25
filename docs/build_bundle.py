"""Bundle the Fortis engine + inventories into one zip for the browser (Pyodide).

The demo page (``docs/index.html``) fetches this zip and unpacks it into Pyodide's
in-browser filesystem, then imports ``src.fortis`` and runs derivations entirely
client-side — no server. Re-run this whenever the engine or inventories change:

    python docs/build_bundle.py
"""

import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(__file__).resolve().parent / "fortis_bundle.zip"


def build() -> None:
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.joinpath("src").rglob("*.py")):
            archive.write(path, path.relative_to(ROOT))
        for path in sorted(ROOT.joinpath("inventories").iterdir()):
            if path.is_file():
                archive.write(path, path.relative_to(ROOT))
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build()
