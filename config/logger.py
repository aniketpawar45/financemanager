import logging
import sys

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("finance_os.log", encoding="utf-8"), 
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("FinanceOS")

def log_error(context_message, exception):
    logger.error(f"[ERROR] {context_message}: {str(exception)}", exc_info=True)
