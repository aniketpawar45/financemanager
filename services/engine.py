import re, httpx, dateparser
from rapidfuzz import process
from data.storage import get_data
from config.settings import GROQ_API_KEY

def parse_smart_text(text):
    text = text.strip(); words = text.split(); custom_date = None
    if any(words[0].lower().startswith(t) for t in ["yesterday", "today", "last"]):
        dt = dateparser.parse(words[0], settings={'PREFER_DATES_FROM': 'past', 'TIMEZONE': 'Asia/Kolkata'})
        if dt: custom_date = dt.strftime("%d-%m-%Y"); text = " ".join(words[1:])
    amt = re.search(r'\d+(\.\d+)?', text)
    if not amt: return None, None, None
    return re.sub(r'\d+(\.\d+)?', '', text).strip().title(), float(amt.group()), custom_date

async def fuzzy_match_category(item):
    data = await get_data()
    past = {r["itemName"].lower(): r["categoryName"] for r in data}
    match = process.extractOne(item.lower(), list(past.keys()), score_cutoff=82)
    return past[match[0]] if match else None

async def transcribe(buf):
    async with httpx.AsyncClient() as c:
        r = await c.post(
            "https://api.groq.com/openai/v1/audio/transcriptions", 
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, 
            files={"file": ("v.ogg", buf)}, 
            data={"model": "whisper-large-v3"}
        )
        return r.json().get("text") if r.status_code == 200 else None
