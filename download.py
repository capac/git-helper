# ingest/download.py
import httpx
from pathlib import Path

URL = "https://github.com/progit/progit2/releases/download/2.1.450/progit.html"
OUT = Path("data/progit.html")

def download():
    OUT.parent.mkdir(exist_ok=True)
    if OUT.exists():
        print("Already downloaded, skipping.")
        return
    r = httpx.get(URL, follow_redirects=True, timeout=60)
    r.raise_for_status()
    OUT.write_bytes(r.content)
    print(f"Saved {len(r.content)/1e6:.1f} MB to {OUT}")


if __name__ == "__main__":
    download()
