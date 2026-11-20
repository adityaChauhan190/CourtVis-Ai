"""Quick test to see which Groq models work for the evidence graph."""
import os
# GROQ_API_KEY is read from environment variable or .env
if 'GROQ_API_KEY' not in os.environ:
    from dotenv import load_dotenv
    load_dotenv()

from groq import Groq

client = Groq(api_key=os.environ['GROQ_API_KEY'])

MODELS = [
    'llama-3.3-70b-versatile',
    'llama-3.1-8b-instant',
    'llama3-8b-8192',
    'qwen/qwen3.6-27b',
]

for model in MODELS:
    try:
        r = client.chat.completions.create(
            model=model,
            messages=[{'role': 'user', 'content': 'Return ONLY this JSON, nothing else: {"test": true}'}],
            max_tokens=100,
            temperature=0.1,
        )
        content = (r.choices[0].message.content or '').strip()
        print(f'[OK] {model}: {repr(content[:80])}')
    except Exception as e:
        print(f'[FAIL] {model}: {type(e).__name__}: {e}')
