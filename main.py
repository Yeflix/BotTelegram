import logging
from telegram.ext import ApplicationBuilder, ContextTypes
from bot_interactivo import start, button_click
from descargaVideos import download_video
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Configuración del logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)
TOKEN = "8008509821:AAFqFhLDqs4d8jNDJk1YrIQuIrC6nygNn_M"

def main() -> None:
    application = ApplicationBuilder()\
        .token(TOKEN)\
        .read_timeout(1200)\
        .write_timeout(1200)\
        .build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    application.add_handler(CallbackQueryHandler(button_click))

    application.run_polling()

if __name__ == '__main__':
    main()
