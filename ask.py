"""Answer one question from the stored chunks, with citations.
Usage:  python ask.py "How do I set up a UPI PIN on WhatsApp?"
"""
import os, sys, time
import anthropic, chromadb
from dotenv import load_dotenv

load_dotenv()                                  # reads ANTHROPIC_API_KEY and MODEL from .env
MODEL = os.environ["MODEL"]                    # copy the model id from hello.py into .env
TOP_K = 5

SYSTEM = """You help WhatsApp users in India with payment questions.
Rules:
1. Answer ONLY from the numbered sources given. Cite each claim like [2].
2. If the sources don't answer the question, say you can't tell from WhatsApp's help pages,
   and point the user to their bank or to WhatsApp support (Settings > Help). Do not guess steps.
3. If an official source (WhatsApp, NPCI, RBI, bank) and a third-party source disagree,
   give the official answer and mention the disagreement.
4. You cannot see the user's account or transactions. Never ask for a UPI PIN, OTP or card number.
5. Questions not about WhatsApp payments: decline politely.
Keep answers short: steps as a numbered list, then the citations."""

collection = chromadb.PersistentClient(path="chroma_db").get_collection("wa_sources")
claude = anthropic.Anthropic()

def answer(question):
    t0 = time.time()
    hits = collection.query(query_texts=[question], n_results=TOP_K)
    docs, metas = hits["documents"][0], hits["metadatas"][0]
    context = "\n\n".join(
        f"[{i+1}] {m['title']} ({m['publisher']}, {m['type']})\n{d}"
        for i, (d, m) in enumerate(zip(docs, metas)))
    msg = claude.messages.create(
        model=MODEL, max_tokens=2000, system=SYSTEM,
        messages=[{"role": "user", "content": f"Sources:\n{context}\n\nQuestion: {question}"}])
    return {
        # newer models may return a "thinking" block first; keep only the text blocks
        "answer": "".join(b.text for b in msg.content if b.type == "text"),
        "retrieved": [m["source_id"] for m in metas],
        "urls": [m["url"] for m in metas],
        "latency_s": round(time.time() - t0, 2),
        "input_tokens": msg.usage.input_tokens,
        "output_tokens": msg.usage.output_tokens,
    }

if __name__ == "__main__":
    r = answer(" ".join(sys.argv[1:]))
    print(r["answer"])
    print("\nSources:")
    for i, (sid, url) in enumerate(zip(r["retrieved"], r["urls"]), 1):
        print(f"  [{i}] {sid}  {url}")
    print(f"\n{r['latency_s']} s, {r['input_tokens']} in / {r['output_tokens']} out tokens")