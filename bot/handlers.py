import io, dateparser, os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from data.storage import save_expense, get_data, hard_delete, get_categories
from services.engine import parse_smart_text, fuzzy_match_category, transcribe
from services.chart import generate_chart
from bot.state import pending, delete_state
from bot.keyboards import build_delete_keyboard
from config.logger import log_error
from config.settings import get_ist_now

# --- SECURITY LAYER ---
AUTHORIZED_USERS = {int(x) for x in os.getenv("AUTHORIZED_USER_IDS", "").split(",")}


async def is_authorized(update):
    if update.effective_chat.id not in AUTHORIZED_USERS:
        await update.message.reply_text("🚫 Access Denied.")
        return False
    return True


async def handle_text_pipeline(update, context, text, is_voice=False):
    if not await is_authorized(update): return
    try:
        uid = update.effective_chat.id
        item, amt, date = parse_smart_text(text)
        if not item: await update.message.reply_text("Try: 'Milk 40'"); return

        cat = await fuzzy_match_category(item)
        if cat:
            msg = await update.message.reply_text(f"⚡ *Auto-Detected:* 🟢 {cat}\n⏳ _Saving..._", parse_mode="Markdown")
            await save_expense(item, cat, amt, date)
            await msg.edit_text(f"✅ *Saved Successfully!*\n🛒 {item}\n💰 ₹{amt}\n📂 🟢 {cat}\n📅 {date}",
                                parse_mode="Markdown")
            return

        pending[uid] = {"itemName": item, "expenseAmount": amt, "customDate": date}
        cats = await get_categories() or ["Food", "Travel", "Shopping", "Bills"]
        kb = [[InlineKeyboardButton(f"🔴 {c}", callback_data=f"cat|{c}")] for c in cats]
        await update.message.reply_text(f"Got it! *{item}* for ₹*{amt}*.\n\nSelect category: 🗂️",
                                        reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    except Exception as e:
        log_error("Pipeline failure", e)


async def callback_handler(update, context):
    try:
        q = update.callback_query;
        await q.answer();
        uid = q.message.chat_id;
        data = q.data
        if data.startswith("cat|"):
            cat = data.split("|")[1]
            if uid not in pending: return
            item, amt, date = pending[uid]["itemName"], pending[uid]["expenseAmount"], pending[uid]["customDate"]
            del pending[uid]
            await q.edit_message_text(f"You selected 🟢 *{cat}*.\n\n⏳ _Saving..._", parse_mode="Markdown")
            await save_expense(item, cat, amt, date)
            await q.edit_message_text(f"✅ *Saved Successfully!*\n🛒 {item}\n💰 ₹{amt}\n📂 🟢 {cat}\n📅 {date}",
                                      parse_mode="Markdown")
        elif data.startswith("del|"):
            if data == "del|confirm":
                await q.edit_message_text("⏳ Syncing...");
                await hard_delete(list(delete_state[uid]["selectedIds"]));
                await q.edit_message_text("✅ Deleted.")
            else:
                row = int(data.split("|")[1])
                if row in delete_state[uid]["selectedIds"]:
                    delete_state[uid]["selectedIds"].remove(row)
                else:
                    delete_state[uid]["selectedIds"].add(row)
                await q.edit_message_reply_markup(reply_markup=build_delete_keyboard(uid, delete_state))
    except Exception as e:
        if "Message is not modified" not in str(e): log_error("Callback failure", e)


async def report_handler(update, context):
    if not await is_authorized(update): return
    try:
        query = " ".join(context.args) if context.args else "today"
        target_dt = dateparser.parse(query, settings={'PREFER_DATES_FROM': 'past', 'TIMEZONE': 'Asia/Kolkata',
                                                      'RELATIVE_BASE': get_ist_now()})
        if not target_dt: await update.message.reply_text("❌ Could not understand date."); return

        data = await get_data()
        is_month = query.lower() in ["june", "jun", "july", "jul", "may", "april", "apr", "mar", "feb", "jan", "aug",
                                     "sep", "oct", "nov", "dec"] or query.isdigit()
        target_month = target_dt.strftime("%m")
        target_str = target_dt.strftime("%d-%m-%Y")

        filtered = [r for r in data if (len(str(r.get('expenseDate', '')).split('-')) >= 2 and (
            r['expenseDate'].split('-')[1] == target_month if is_month else r['expenseDate'] == target_str))]

        if not filtered: await update.message.reply_text(f"📭 No expenses found for {query}."); return
        total = sum(r["expenseAmount"] for r in filtered)
        lines = [f"• {r['expenseDate']} | {r['itemName']} | ₹{r['expenseAmount']}" for r in filtered]
        await update.message.reply_text(
            f"📊 REPORT: {target_dt.strftime('%B %Y') if is_month else target_str}\n\n" + "\n".join(
                lines) + f"\n\n💰 *Total:* ₹{total:.2f}", parse_mode="Markdown")
    except Exception as e:
        log_error("Report failure", e)


# Helper Wrappers
async def message_handler(update, context): await handle_text_pipeline(update, context, update.message.text)


async def voice_handler(update, context):
    try:
        buf = io.BytesIO()
        await (await context.bot.get_file(update.message.voice.file_id)).download_to_memory(buf)
        text = await transcribe(buf)
        if text: await handle_text_pipeline(update, context, text, True)
    except Exception as e:
        log_error("Voice failure", e)


async def chart_handler(update, context):
    try:
        msg = await update.message.reply_text("🎨 Rendering chart...")
        data = await get_data();
        totals = {}
        for r in data: totals[r["categoryName"]] = totals.get(r["categoryName"], 0) + r["expenseAmount"]
        chart_buffer = await generate_chart(totals)
        if chart_buffer:
            await msg.delete(); await update.message.reply_photo(chart_buffer)
        else:
            await msg.edit_text("❌ Could not render.")
    except Exception as e:
        log_error("Chart failure", e)


async def delete_handler(update, context):
    try:
        uid = update.effective_chat.id;
        data = await get_data()
        delete_state[uid] = {"targetRows": data[-5:], "selectedIds": set()}
        await update.message.reply_text("Select entries to delete:",
                                        reply_markup=build_delete_keyboard(uid, delete_state))
    except Exception as e:
        log_error("Delete failure", e)


async def help_handler(update, context): await update.message.reply_text(
    "🤖 **Finance OS**\n\n• Log: 'Milk 40'\n• Voice: Use mic\n• /report [today/yesterday/June]\n• /chart /delete /help")