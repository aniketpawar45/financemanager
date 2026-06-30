import os, threading, datetime
from flask import Flask
from waitress import serve
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, CommandHandler, filters

from config.settings import BOT_TOKEN, IST
from config.logger import logger, log_error
from bot.handlers import message_handler, voice_handler, chart_handler, callback_handler, delete_handler, report_handler, help_handler
from services.scheduler import nightly_nag_job

flask_app = Flask(__name__)

@flask_app.route('/')
def health_check():
    return "Finance OS Web Service is active. Telegram Bot running in background.", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    serve(flask_app, host="0.0.0.0", port=port)

async def post_init(app):
    await app.bot.set_my_commands([
        ("report", "Report"), 
        ("chart", "Chart"), 
        ("delete", "Delete"), 
        ("help", "Help")
    ])

def main():
    logger.info("Booting Finance OS (Production Mode)...")
    
    threading.Thread(target=run_web, daemon=True).start()
    
    try:
        app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
        
        target_time = datetime.time(hour=22, minute=0, tzinfo=IST)
        app.job_queue.run_daily(nightly_nag_job, target_time)

        app.add_handlers([
            CommandHandler("chart", chart_handler), 
            CommandHandler("delete", delete_handler), 
            CommandHandler("report", report_handler), 
            CommandHandler("help", help_handler),
            CallbackQueryHandler(callback_handler), 
            MessageHandler(filters.VOICE, voice_handler),
            MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
        ])
        app.run_polling()
    except Exception as e:
        log_error("Critical App Failure", e)
