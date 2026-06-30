from data.storage import get_data
from config.settings import ADMIN_CHAT_ID, get_ist_now
from config.logger import log_error

async def nightly_nag_job(context):
    try:
        if not ADMIN_CHAT_ID or ADMIN_CHAT_ID == "PUT_YOUR_PERSONAL_TELEGRAM_ID_HERE": return

        today_str = get_ist_now().strftime("%d-%m-%Y")
        data = await get_data()
        
        spent_today = sum(r["expenseAmount"] for r in data if r["expenseDate"] == today_str)

        if spent_today == 0:
            await context.bot.send_message(
                chat_id=int(ADMIN_CHAT_ID),
                text="🌙 **Accountant Nag:** You have logged ₹0 today.\n\nReply with anything you bought, or ignore this if you actually spent nothing!"
            )
    except Exception as e:
        log_error("Failed nightly nag job execution", e)
