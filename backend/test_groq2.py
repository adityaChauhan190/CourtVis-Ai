"""Test which Groq models actually work and return JSON properly."""
import os
# GROQ_API_KEY is read from environment variable or .env
if 'GROQ_API_KEY' not in os.environ:
    from dotenv import load_dotenv
    load_dotenv()

from groq import Groq

client = Groq(api_key=os.environ['GROQ_API_KEY'])

# List available models first
print("=== Available Models ===")
try:
    models = client.models.list()
    for m in models.data:
        print(f"  {m.id}")
except Exception as e:
    print(f"Could not list models: {e}")

print("\n=== Testing JSON output ===")
MODELS = [
    'llama-3.3-70b-versatile',
    'llama-3.1-8b-instant',
    'llama3-8b-8192',
    'llama3-70b-8192',
    'gemma2-9b-it',
    'gemma-7b-it',
    'mixtral-8x7b-32768',
    'qwen/qwen3.6-27b',
    'qwen-qwq-32b',
    'meta-llama/llama-4-scout-17b-16e-instruct',
    'meta-llama/llama-4-maverick-17b-128e-instruct',
    'compound-beta',
    'compound-beta-mini',
]

for model in MODELS:
    try:
        r = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': 'You are a JSON API. Respond ONLY with valid JSON. No explanations, no thinking, no markdown.'},
                {'role': 'user', 'content': 'Return this exact JSON: {"test": true, "status": "ok"}'}
            ],
            max_tokens=200,
            temperature=0.0,
        )
        content = (r.choices[0].message.content or '').strip()
        print(f'[OK] {model}: {repr(content[:100])}')
    except Exception as e:
        err = str(e)[:120]
        print(f'[FAIL] {model}: {type(e).__name__}: {err}')
