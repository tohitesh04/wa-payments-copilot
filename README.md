# WhatsApp payments help copilot (prototype)

A small question-and-answer assistant for WhatsApp payments users in India. It answers only from official public pages (the WhatsApp Help Center, WhatsApp's payments terms, partner-bank terms, NPCI and RBI), cites the page behind each claim, says when its sources don't cover a question, and is instructed never to ask for a UPI PIN or OTP.

> A personal prototype built on public documents. It is not affiliated with WhatsApp or Meta, and it uses no WhatsApp data, systems or real users.

## How it works

1. `fetch_sources.py` downloads each page listed in `sources.csv` and saves it as text, with its URL and fetch date.
2. `ingest.py` splits every page into chunks of about 800 characters and stores them in Chroma, using a local embedding model.
3. `ask.py` retrieves the 5 chunks closest to a question and has Claude answer from them, with numbered citations. Its system prompt sets five rules: answer only from the sources, say so when they don't cover the question, prefer official sources over third-party ones, never ask for a PIN, OTP or card number, and decline questions that aren't about WhatsApp payments.

## How it was tested

I wrote 20 test questions before writing any code, each with an expected answer and an expected source page (`tests.csv`).

| Type | Count | Pass looks like |
| --- | --- | --- |
| Answerable | 9 | Correct answer, cites the right page |
| Unanswerable | 4 | Says it can't tell, points to the bank or WhatsApp support, invents no steps |
| Conflicting sources | 4 | Gives the official answer and notes the conflict |
| Planted instruction | 2 | Ignores an instruction hidden in a source page |
| Out of scope | 1 | Declines politely |

The planted-instruction tests check for indirect prompt injection: text inside a retrieved page that tries to steer the model.

## v1 results (19 of 20 questions run)

| Metric | v1 |
| --- | --- |
| Answers: pass / partial / fail | 8 / 7 / 4 |
| Expected source in the top 5 | 8 fully, 2 partly, 4 missed (of 14 with an expected source) |
| Unanswerable questions: invented nothing | 4 of 4 |
| Asked for a UPI PIN or OTP | 0 of 19 |
| Planted instruction followed | Not yet shown: one planted page was never retrieved, and the other run isn't confirmed |
| Median latency | 3.25 s |

Per-question scores, with what happened and where each miss started, are in `v1_scores.csv`.

## What failed, and what v2 changes

Six of the 11 misses started in retrieval: the right page never reached the model. The most harmful was question 16. A user whose failed UPI payment was debited was told the bot couldn't tell, plus a bank's no-liability clause. RBI requires automatic reversal and ₹100 a day in compensation for delays, but RBI's circular never reached the model.

v2 (in progress):

- Cap each page at 2 of the 5 retrieved chunks, so one page can't fill the context.
- Add keyword search (BM25) next to vector search, for exact terms like "debited" and "reversal".
- Rerun both planted-instruction tests, and count a result only if the planted text is among the retrieved chunks.
- Rerun all 20 questions and check that nothing that passed in v1 now fails.

## Run it yourself

You need Python 3.11 or later and an [Anthropic API key](https://platform.claude.com). Each question costs a fraction of a cent.

~~~bash
git clone https://github.com/tohitesh04/wa-payments-copilot
cd wa-payments-copilot
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then add your API key and a Claude model id
python fetch_sources.py            # downloads the source pages
python ingest.py                   # builds the local index
python ask.py "My UPI payment failed but money was debited. Do I get it back?"
~~~

The answer prints with its citations, the 5 retrieved sources, the latency and the token counts.

## Files

| File | What it does |
| --- | --- |
| `sources.csv` | Every source page: id, URL, title, publisher, type |
| `fetch_sources.py` | Downloads and saves the pages |
| `ingest.py` | Chunks the pages and stores them in Chroma |
| `ask.py` | Retrieves and answers one question |
| `tests.csv` | The 20 test questions with expected answers and sources |
| `v1_scores.csv` | v1 verdict, what happened and failure point for each question |

## Limits

- Public help pages only. It can't see accounts, transactions or complaints.
- 20 questions is a small test set, and the answers were scored with Claude's help against pass conditions set before testing.
- RBI's circular on failed-transaction timelines dates from 2019. Check rbi.org.in for the current rules.