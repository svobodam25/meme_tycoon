"""Build and smoke-test the standalone Windows release without touching player saves."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED


ROOT = Path(__file__).resolve().parent


def main():
    if sys.platform != "win32":
        raise SystemExit("Build this Windows release on Windows.")
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
                   cwd=ROOT, check=True)
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
                    "--onefile", "--windowed", "--name", "MemeTycoon", "main.py"],
                   cwd=ROOT, check=True)
    executable = ROOT / "dist" / "MemeTycoon.exe"
    with tempfile.TemporaryDirectory(prefix="meme-tycoon-release-") as directory:
        temporary = Path(directory)
        screenshot = temporary / "smoke.png"
        env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy",
                   LOCALAPPDATA=str(temporary))
        subprocess.run([str(executable), "--smoke-test", "--save", str(temporary / "save.json"),
                        "--screenshot", str(screenshot)], cwd=temporary, env=env,
                       creationflags=subprocess.CREATE_NO_WINDOW, check=True, timeout=60)
        if not screenshot.exists() or screenshot.stat().st_size == 0:
            raise RuntimeError("The packaged game did not render its smoke-test screenshot.")
        if (temporary / "save.json").exists():
            raise RuntimeError("Smoke test unexpectedly created a save.")
    archive = ROOT / "dist" / "MemeTycoon-windows-x64.zip"
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
        for path in (executable, ROOT / "README.md", ROOT / "LICENSE"):
            bundle.write(path, path.name)
    checksums = ROOT / "dist" / "SHA256SUMS.txt"
    checksums.write_text("".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
        for path in (executable, archive)), encoding="utf-8")
    print(f"Release ready: {executable}")
    print(f"ZIP ready: {archive}")


if __name__ == "__main__":
    main()
