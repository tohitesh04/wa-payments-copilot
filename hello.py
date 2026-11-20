import time

import anthropic
from dotenv import load_dotenv

MODEL = "claude-haiku-5-5"
QUESTION = "In one sentence, what is UPI and why is it popular in India?"

load_dotenv()  # reads ANTHROPIC_API_KEY from .env

client = anthropic.Anthropic()

start = time.perf_counter()
response = client.messages.create(
    model=MODEL,
    max_tokens=300,
    messages=[{"role": "user", "content": QUESTION}],
)
latency = time.perf_counter() - start

print(f"Q: {QUESTION}")
print(f"A: {response.content[0].text}")
print(f"Input tokens:  {response.usage.input_tokens}")
print(f"Output tokens: {response.usage.output_tokens}")
print(f"Latency:       {latency:.2f}s")
