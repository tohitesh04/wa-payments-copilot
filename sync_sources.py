"""Update sources.csv from the .txt files in data/sources/.
Each file: line 1 = URL, line 2 = date fetched, then the page text.
Run from the repo folder:  python sync_sources.py
"""
import csv, re
from pathlib import Path
from urllib.parse import urlparse

CSV, DIR = Path("sources.csv"), Path("data/sources")
COLS = ["id", "url", "title", "publisher", "date_fetched", "type", "file"]
PUBLISHERS = {"faq.whatsapp.com": "WhatsApp Help Center", "whatsapp.com": "WhatsApp",
              "npci.org.in": "NPCI", "rbi.org.in": "RBI"}

def publisher(url):
    host = urlparse(url).netloc.removeprefix("www.")
    for dom, name in PUBLISHERS.items():
        if host == dom or host.endswith("." + dom):
            return name, "official"
    return host, "third_party"

rows = {}
if CSV.exists():
    with CSV.open(newline="", encoding="utf-8") as f:
        rows = {r["id"]: r for r in csv.DictReader(f)}

added, updated = [], []
for txt in sorted(DIR.glob("*.txt")):
    sid = txt.stem
    if "planted" in sid:
        print(f"SKIP  {sid}: planted-instruction copy, kept out of sources.csv")
        continue
    lines = txt.read_text(encoding="utf-8").splitlines()
    if len(lines) < 3 or not lines[0].strip().startswith("http"):
        print(f"BAD   {txt.name}: line 1 must be the URL, line 2 the date")
        continue
    url, date = lines[0].strip(), lines[1].strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        print(f"WARN  {txt.name}: date '{date}' is not YYYY-MM-DD")
    title = next((l.strip() for l in lines[2:] if l.strip()), "")[:120]
    pub, kind = publisher(url)
    new = {"id": sid, "url": url, "date_fetched": date, "file": txt.as_posix()}
    if sid in rows:
        row = rows[sid]
        if any(row.get(k, "") != v for k, v in new.items()):
            row.update(new); updated.append(sid)
    else:
        rows[sid] = {**new, "title": title, "publisher": pub, "type": kind}
        added.append(sid)

with CSV.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
    w.writeheader(); w.writerows(rows.values())

missing = [i for i, r in rows.items() if not Path(r["file"]).exists()]
print(f"\nAdded {len(added)}: {', '.join(added) or '-'}")
print(f"Updated {len(updated)}: {', '.join(updated) or '-'}")
print(f"In csv but no .txt yet ({len(missing)}): {', '.join(missing) or '-'}")
print("Check the titles of added rows in sources.csv; they're guessed from the first text line.")
