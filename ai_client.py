import os
import re
import json
import time
import random
import urllib.parse
import urllib.request
import urllib.error

import config
from logger import ok, warn

def extract_json(text):
    text = str(text).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        text = text[first:last+1]
    return json.loads(text)

def call_gemini(prompt, model, debug=False):
    if not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set.")

    url = config.GEMINI_API_URL_TEMPLATE.format(model=urllib.parse.quote(model, safe="")) + "?key=" + urllib.parse.quote(config.GEMINI_API_KEY)

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "sermon-ingest/0.1"},
        method="POST",
    )

    if debug:
        print(f"Gemini request using {model}, timeout {config.AI_TIMEOUT_SECONDS}s...", flush=True)

    with urllib.request.urlopen(req, timeout=config.AI_TIMEOUT_SECONDS) as r:
        data = json.loads(r.read().decode("utf-8", errors="replace"))

    if data.get("error"):
        raise RuntimeError(f"Gemini API error: {data['error']}")

    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates: {data}")

    parts = candidates[0].get("content", {}).get("parts", [])
    content = "".join(part.get("text", "") for part in parts if isinstance(part, dict))

    if not content.strip():
        raise RuntimeError(f"Gemini returned empty content: {data}")

    return extract_json(content)

def call_openrouter(prompt, model, debug=False):
    if not config.OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    req = urllib.request.Request(
        config.OPENROUTER_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost/sermon-ingest",
            "X-Title": "Sermon Ingest",
        },
        method="POST",
    )

    if debug:
        print(f"OpenRouter request using {model}, timeout {config.AI_TIMEOUT_SECONDS}s...", flush=True)

    with urllib.request.urlopen(req, timeout=config.AI_TIMEOUT_SECONDS) as r:
        data = json.loads(r.read().decode("utf-8", errors="replace"))

    if data.get("error"):
        raise RuntimeError(f"OpenRouter API error: {data['error']}")

    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError(f"OpenRouter returned no choices: {data}")

    content = choices[0].get("message", {}).get("content", "")
    if isinstance(content, list):
        content = "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)

    return extract_json(content)

def call_ai(prompt, provider, model, debug=False):
    models_to_try = [model]
    if provider == "gemini":
        for fallback in ["gemini-2.5-flash", "gemini-2.0-flash"]:
            if fallback not in models_to_try:
                models_to_try.append(fallback)

    last_error = None
    for m in models_to_try:
        for attempt in range(1, config.AI_MAX_RETRIES + 1):
            try:
                if debug or len(models_to_try) > 1:
                    print(f"AI call: model={m} provider={provider} (attempt {attempt}/{config.AI_MAX_RETRIES})", flush=True)
                
                if provider == "gemini":
                    return call_gemini(prompt, m, debug)
                elif provider == "openrouter":
                    return call_openrouter(prompt, m, debug)
                else:
                    raise RuntimeError(f"Unknown AI_PROVIDER: {provider}")
            except Exception as e:
                last_error = e
                warn(f"AI model {m} failed: {e}")
                
                # Check for daily quota exhaustion
                err_msg = str(e)
                if hasattr(e, 'read'):
                    try:
                        err_msg += " " + e.read().decode("utf-8", errors="replace")
                    except:
                        pass
                
                is_quota_exhausted = False
                if "Quota exceeded" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    is_quota_exhausted = True
                    
                if is_quota_exhausted:
                    print(f"Daily quota limit exhausted for {m}. Immediately failing over.", flush=True)
                    break # Break retry loop for this model, moving to fallback model or raising error
                
                if attempt < config.AI_MAX_RETRIES:
                    is_429 = False
                    if isinstance(e, urllib.error.HTTPError) and e.code == 429:
                        is_429 = True
                    elif "429" in str(e):
                        is_429 = True
                        
                    if is_429:
                        wait = 20.0 + random.uniform(1.0, 5.0)
                        print(f"Rate limit hit (429). Waiting {wait:.1f}s for reset...", flush=True)
                    else:
                        wait = config.AI_BASE_SLEEP_SECONDS * attempt + random.uniform(0.1, 1.0)
                        print(f"Retrying model {m} in {wait:.1f}s...")
                    time.sleep(wait)
                else:
                    print(f"Model {m} failed all retries.")
    
    raise RuntimeError(f"AI failed on all attempted models. Last error: {last_error}")
