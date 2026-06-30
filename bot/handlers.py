import io
from telegram import InlineKeyboardMarkup
from telegram.ext import ContextTypes
from data.storage import save_expense, get_data, hard_delete, get_categories, DriveAccessError
from services.engine import parse_smart_text, fuzzy_match_category, transcribe
from services.chart import generate_chart
from bot.state import pending, delete_state
from bot.keyboards import build_delete_keyboard, build_category_keyboard
from config.logger import log_error

async def handle_text_pipeline(update, context, text, is_voice=False):
    try:
        uid = update.effective_chat.id
        item, amt, date = parse_smart_text(text)
        if not item: 
            await update.message.reply_text("Try: 'Milk 40'")
            return
        
        cat = await fuzzy_match_category(item)
        if cat:
            await save_expense(item, cat, amt, date)
            await update.message.reply_text(f"⚡ Saved: {item} → {cat} ₹{amt}")
            return
        
        pending[uid] = {"itemName": item, "expenseAmount": amt, "customDate": date}
        cats = await get_categories() or ["Food", "Travel", "Shopping", "Bills"]
        kb = build_category_keyboard(cats)
        
        await update.message.reply_text(
            f"Select category for {item} (₹{amt}):", 
            reply_markup=InlineKeyboardMarkup(kb)
        )
    except DriveAccessError as e:
        await update.message.reply_text(f"⚠️ **Storage Error:**\n{str(e)}")
    except Exception as e:
        log_error("Text pipeline failure", e)
        await update.message.reply_text("❌ An internal error occurred.")

async def message_handler(update, context): 
    await handle_text_pipeline(update, context, update.message.text)

async def voice_handler(update, context):
    try:
        buf = io.BytesIO()
        await (await context.bot.get_file(update.message.voice.file_id)).download_to_memory(buf)
        text = await transcribe(buf)
        if text: await handle_text_pipeline(update, context, text, True)
        else: await update.message.reply_text("❌ Transcription failed.")
    except Exception as e:
        log_error("Voice processing failure", e)

async def chart_handler(update, context):
    try:
        msg = await update.message.reply_text("🎨 Rendering chart...")
        data = await get_data(); totals = {}
        for r in data: totals[r["categoryName"]] = totals.get(r["categoryName"], 0) + r["expenseAmount"]
        
        chart_buffer = await generate_chart(totals)
        if chart_buffer:
            await msg.delete(); await update.message.reply_photo(chart_buffer)
        else: 
            await msg.edit_text("❌ Could not render chart.")
    except Exception as e:
        log_error("Chart render failure", e)

async def callback_handler(update, context):
    try:
        q = update.callback_query; await q.answer(); uid = q.message.chat_id; data = q.data
        if data.startswith("cat|"):
            _, cat = data.split("|")
            await save_expense(pending[uid]["itemName"], cat, pending[uid]["expenseAmount"], pending[uid]["customDate"])
            await q.edit_message_text(f"Saved: {pending[uid]['itemName']} → {cat}")
        elif data.startswith("del|"):
            if data == "del|confirm":
                await q.edit_message_text("⏳ Syncing..."); await hard_delete(list(delete_state[uid]["selectedIds"]))
                await q.edit_message_text("✅ Deleted.")
            else:
                row = int(data.split("|")[1])
                if row in delete_state[uid]["selectedIds"]: delete_state[uid]["selectedIds"].remove(row)
                else: delete_state[uid]["selectedIds"].add(row)
                await q.edit_message_reply_markup(reply_markup=build_delete_keyboard(uid, delete_state))
    except Exception as e:
        log_error("Callback handler failure", e)

async def delete_handler(update, context):
    try:
        uid = update.effective_chat.id
        data = await get_data()
        delete_state[uid] = {"targetRows": data[-5:], "selectedIds": set()}
        await update.message.reply_text("Select entries to delete:", reply_markup=build_delete_keyboard(uid, delete_state))
    except DriveAccessError as e:
        await update.message.reply_text(f"⚠️ **Storage Error:**\n{str(e)}")
    except Exception as e:
        log_error("Delete handler failure", e)

async def report_handler(update, context):
    try:
        data = await get_data()
        total = sum(r["expenseAmount"] for r in data)
        lines = [f"{r['expenseDate']} | {r['itemName']} | ₹{r['expenseAmount']} | {r['categoryName']}\n" for r in data[-10:]]
        await update.message.reply_text(f"📊 REPORT\n\nTotal: ₹{total:.2f}\n\n" + "".join(lines))
    except DriveAccessError as e:
        await update.message.reply_text(f"⚠️ **Storage Error:**\n{str(e)}")
    except Exception as e:
        log_error("Report handler failure", e)

async def help_handler(update, context):
    await update.message.reply_text("🤖 **Finance OS**\n\n• Log: 'Milk 40'\n• Voice: Use mic\n• /report /chart /delete /help")
