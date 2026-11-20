"""Download each page in sources.csv to data/sources/<id>.txt.
Line 1 = URL, line 2 = fetch date, then the page text. Rows with an empty url are skipped.
Run from the repo root with the venv active:  python fetch_sources.py
Needs: pip install requests beautifulsoup4
"""
import csv, datetime, pathlib, sys
import requests
from bs4 import BeautifulSoup

today = datetime.date.today().isoformat()
rows = list(csv.DictReader(open("sources.csv", newline="", encoding="utf-8")))
pathlib.Path("data/sources").mkdir(parents=True, exist_ok=True)

for r in rows:
    if not r["url"].strip():
        print(f"SKIP  {r['id']} (no url yet)")
        continue
    try:
        resp = requests.get(r["url"], timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for t in soup(["script", "style", "nav", "header", "footer", "noscript"]):
            t.decompose()
        text = "\n".join(l.strip() for l in soup.get_text("\n").splitlines() if l.strip())
        pathlib.Path(r["file"]).write_text(f"{r['url']}\n{today}\n{text}\n", encoding="utf-8")
        r["date_fetched"] = today
        print(f"OK    {r['id']}  ({len(text)} chars)")
    except Exception as e:
        print(f"FAIL  {r['id']}: {e}  -> paste the page text by hand into {r['file']}")

with open("sources.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader(); w.writerows(rows)
