import io, os, json, dateparser
import google.generativeai as genai
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from data.storage import save_expense, get_data, hard_delete, get_categories
from services.engine import fuzzy_match_category, transcribe
from services.chart import generate_chart
from bot.state import pending, delete_state
from bot.keyboards import build_delete_keyboard
from config.logger import log_error
from config.settings import get_ist_now

# --- AI SETUP ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

AUTHORIZED_USERS = {int(x) for x in os.getenv("AUTHORIZED_USER_IDS", "").split(",")}

async def is_authorized(update):
    if update.effective_chat.id not in AUTHORIZED_USERS:
        await update.message.reply_text("🚫 Access Denied.")
        return False
    return True

async def parse_with_ai(text):
    """Uses Gemini to extract financial details."""
    prompt = f"""Extract expense details from: "{text}". 
    Return ONLY a JSON object with keys: "item" (string), "amount" (float), "date" (string: DD-MM-YYYY).
    If no date is mentioned, use today: {get_ist_now().strftime('%d-%m-%Y')}.
    Example input: 'Spent 500 on dinner' -> {{"item": "Dinner", "amount": 500.0, "date": "{get_ist_now().strftime('%d-%m-%Y')}"}}"""
    
    response = model.generate_content(prompt)
    try:
        data = json.loads(response.text.replace("```json", "").replace("```", "").strip())
        return data.get('item'), data.get('amount'), data.get('date')
    except: return None, None, None

async def handle_text_pipeline(update, context, text):
    if not await is_authorized(update): return
    try:
        uid = update.effective_chat.id
        item, amt, date = await parse_with_ai(text)
        
        if not item or not amt: 
            await update.message.reply_text("I didn't quite get that. Try: 'Lunch for 200' or 'Auto service 5000 yesterday'")
            return

        cat = await fuzzy_match_category(item)
        if cat:
            msg = await update.message.reply_text(f"⚡ *Parsed:* {item} (₹{amt})\n🟢 {cat}\n⏳ _Saving..._", parse_mode="Markdown")
            await save_expense(item, cat, amt, date)
            await msg.edit_text(f"✅ *Saved!*\n🛒 {item}\n💰 ₹{amt}\n📂 🟢 {cat}\n📅 {date}", parse_mode="Markdown")
            return

        pending[uid] = {"itemName": item, "expenseAmount": amt, "customDate": date}
        cats = await get_categories() or ["Food", "Travel", "Shopping", "Bills"]
        kb = [[InlineKeyboardButton(f"🔴 {c}", callback_data=f"cat|{c}")] for c in cats]
        await update.message.reply_text(f"Got it! *{item}* for ₹*{amt}*.\nSelect category:", 
                                        reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    except Exception as e:
        log_error("Pipeline failure", e)

# --- Existing Handlers ---
async def message_handler(update, context): await handle_text_pipeline(update, context, update.message.text)

async def voice_handler(update, context):
    try:
        buf = io.BytesIO()
        file = await context.bot.get_file(update.message.voice.file_id)
        await file.download_to_memory(buf)
        text = await transcribe(buf)
        if text: await handle_text_pipeline(update, context, text)
        else: await update.message.reply_text("❌ Could not transcribe voice.")
    except Exception as e: log_error("Voice failure", e)

async def callback_handler(update, context):
    try:
        q = update.callback_query; await q.answer(); uid = q.message.chat_id; data = q.data
        if data.startswith("cat|"):
            cat = data.split("|")[1]
            if uid not in pending: return
            item, amt, date = pending[uid]["itemName"], pending[uid]["expenseAmount"], pending[uid]["customDate"]
            del pending[uid]
            await save_expense(item, cat, amt, date)
            await q.edit_message_text(f"✅ *Saved!*\n🛒 {item}\n💰 ₹{amt}\n📂 🟢 {cat}\n📅 {date}", parse_mode="Markdown")
        elif data.startswith("del|"):
            if data == "del|confirm":
                await hard_delete(list(delete_state[uid]["selectedIds"])); await q.edit_message_text("✅ Deleted.")
            else:
                row = int(data.split("|")[1])
                if row in delete_state[uid]["selectedIds"]: delete_state[uid]["selectedIds"].remove(row)
                else: delete_state[uid]["selectedIds"].add(row)
                await q.edit_message_reply_markup(reply_markup=build_delete_keyboard(uid, delete_state))
    except Exception as e: log_error("Callback failure", e)

async def report_handler(update, context):
    if not await is_authorized(update): return
    try:
        query = " ".join(context.args) if context.args else "today"
        target_dt = dateparser.parse(query, settings={'PREFER_DATES_FROM': 'past', 'TIMEZONE': 'Asia/Kolkata', 'RELATIVE_BASE': get_ist_now()})
        if not target_dt: await update.message.reply_text("❌ Could not understand date."); return
        data = await get_data()
        is_month = query.lower() in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        target_month = target_dt.strftime("%m")
        filtered = [r for r in data if (len(str(r.get('expenseDate', '')).split('-')) >= 2 and (r['expenseDate'].split('-')[1] == target_month if is_month else r['expenseDate'] == target_dt.strftime("%d-%m-%Y")))]
        if not filtered: await update.message.reply_text(f"📭 No expenses found for {query}."); return
        total = sum(r["expenseAmount"] for r in filtered)
        lines = [f"• {r['expenseDate']} | {r['itemName']} | ₹{r['expenseAmount']}" for r in filtered]
        await update.message.reply_text(f"📊 REPORT: {target_dt.strftime('%B %Y') if is_month else target_dt.strftime('%d-%m-%Y')}\n\n" + "\n".join(lines) + f"\n\n💰 *Total:* ₹{total:.2f}", parse_mode="Markdown")
    except Exception as e: log_error("Report failure", e)

async def chart_handler(update, context):
    try:
        msg = await update.message.reply_text("🎨 Rendering chart...")
        data = await get_data(); totals = {}
        for r in data: totals[r["categoryName"]] = totals.get(r["categoryName"], 0) + r["expenseAmount"]
        chart_buffer = await generate_chart(totals)
        if chart_buffer: await msg.delete(); await update.message.reply_photo(chart_buffer)
        else: await msg.edit_text("❌ Could not render.")
    except Exception as e: log_error("Chart failure", e)

async def delete_handler(update, context):
    try:
        uid = update.effective_chat.id; data = await get_data()
        delete_state[uid] = {"targetRows": data[-5:], "selectedIds": set()}
        await update.message.reply_text("Select entries to delete:", reply_markup=build_delete_keyboard(uid, delete_state))
    except Exception as e: log_error("Delete failure", e)

async def help_handler(update, context): await update.message.reply_text("🤖 **Finance OS**\n\n• Log: 'Milk 40'\n• Voice: Use mic\n• /report [today/yesterday/June]\n• /chart /delete /help")
