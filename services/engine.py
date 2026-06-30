import re, httpx, dateparser
from rapidfuzz import process
from data.storage import get_data
from config.settings import GROQ_API_KEY, get_ist_now


def parse_smart_text(text):
    text = text.strip()
    today = get_ist_now()
    final_date = today.strftime("%d-%m-%Y")

    # Matches patterns like 26-06, 26-06-2026, 26 June, 26-June
    date_pattern = r'(\d{1,2}[-/]\d{1,2}(?:[-/]\d{2,4})?|\d{1,2}\s(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*)'
    found_date = re.search(date_pattern, text, re.IGNORECASE)

    if found_date:
        dt = dateparser.parse(found_date.group(0), settings={'TIMEZONE': 'Asia/Kolkata', 'DATE_ORDER': 'DMY'})
        if dt:
            final_date = dt.strftime("%d-%m-%Y")
            text = text.replace(found_date.group(0), "").strip()

    amt = re.search(r'\d+(\.\d+)?', text)
    if not amt: return None, None, final_date

    item_name = re.sub(r'\d+(\.\d+)?', '', text).strip().title()
    return item_name, float(amt.group()), final_date


async def fuzzy_match_category(item):
    data = await get_data()
    if not data: return None
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