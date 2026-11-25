"""Split every saved page into chunks and store them in Chroma.
Run from the repo folder:  python ingest.py
Re-run it whenever you add or change a page in data/sources/.
For planted-instruction tests 18-19:  PLANTED=1 python ingest.py
(then run plain python ingest.py again to restore the clean index)
"""
import csv, os
from pathlib import Path
import chromadb

CHUNK_CHARS = 800    # about 150-200 words per chunk
OVERLAP = 150        # characters repeated between neighbouring chunks

def split_into_chunks(text, size=CHUNK_CHARS, overlap=OVERLAP):
    """Pack paragraphs into chunks of about `size` characters."""
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    chunks, current = [], ""
    for p in paras:
        if current and len(current) + len(p) + 1 > size:
            chunks.append(current)
            current = current[-overlap:]          # carry a little context forward
        current = (current + "\n" + p).strip()
        while len(current) > size * 1.5:          # one very long paragraph
            chunks.append(current[:size])
            current = current[size - overlap:]
    if current:
        chunks.append(current)
    return chunks

client = chromadb.PersistentClient(path="chroma_db")   # a folder on disk
try:
    client.delete_collection("wa_sources")             # start clean each run
except Exception:
    pass
collection = client.create_collection("wa_sources")   # default embedding model runs locally

with open("sources.csv", newline="", encoding="utf-8") as f:
    sources = list(csv.DictReader(f))

total = 0
for s in sources:
    path = Path(s["file"])
    planted = path.with_name(path.stem + "-planted.txt")
    if os.getenv("PLANTED") and planted.exists():
        path = planted                                   # swap in the poisoned copy
        print(f"PLANTED copy used for {s['id']}")
    if not path.exists():
        print(f"no file yet: {s['id']}")
        continue
    lines = path.read_text(encoding="utf-8").splitlines()
    text = "\n".join(lines[2:])                         # skip URL and date lines
    chunks = split_into_chunks(text)
    collection.add(
        ids=[f"{s['id']}#{i}" for i in range(len(chunks))],
        documents=chunks,
        metadatas=[{"source_id": s["id"], "title": s["title"], "url": s["url"],
                    "publisher": s["publisher"], "type": s["type"]} for _ in chunks],
    )
    total += len(chunks)
    print(f"{s['id']}: {len(chunks)} chunks")

print(f"\nStored {total} chunks from {len(sources)} sources in chroma_db/")