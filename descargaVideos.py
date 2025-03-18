import logging
import os
import asyncio
import re
import time
from urllib.parse import urlparse, parse_qs
import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import yt_dlp
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configuración del logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)
TOKEN = "8008509821:AAFqFhLDqs4d8jNDJk1YrIQuIrC6nygNn_M"  # Reemplaza con tu token
DOWNLOAD_DIR = os.path.abspath("descargas")  # Ruta absoluta multiplataforma
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
MAX_FILE_SIZE = 40 * 1024 * 1024  # 40MB

# Configura las credenciales de Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("¡Bienvenido al bot! Envíame una URL de video para descargar.")

def sanitize_filename(title):
    # Limpieza agresiva de caracteres especiales
    cleaned = re.sub(r'[^a-zA-Z0-9 \-\_\.]', '', title)
    # Limitar longitud y añadir timestamp único
    return f"{cleaned[:30]}_{int(time.time())}.mp4".strip()

class DownloadProgressBar:
    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.update = update
        self.context = context
        self.start_time = None
        self.message = None

    async def __call__(self, d):
        if d['status'] == 'downloading':
            if self.start_time is None:
                self.start_time = asyncio.get_event_loop().time()
            
            progress_info = f"📥 Descargando...\n\n"
            progress_info += f"Progreso: {d['_percent_str']}\n"
            progress_info += f"Velocidad: {d['_speed_str']}\n"
            progress_info += f"ETA: {d['_eta_str']}"

            if self.message:
                try:
                    await self.message.edit_text(progress_info)
                except telegram.error.BadRequest:
                    self.message = await self.update.message.reply_text(progress_info)
            else:
                self.message = await self.update.message.reply_text(progress_info)

        if d['status'] == 'finished' and self.message:
            try:
                await self.message.delete()
            except telegram.error.BadRequest:
                pass

def upload_to_drive(file_path):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)

    file_metadata = {'name': os.path.basename(file_path)}
    media = MediaFileUpload(file_path, resumable=True)
    
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    service.permissions().create(fileId=file['id'], body={'role': 'reader', 'type': 'anyone'}).execute()
    
    return f"https://drive.google.com/uc?export=download&id={file['id']}"

async def send_video_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE, video_path):
    """Envia el video al chat de Telegram."""
    try:
        await context.bot.send_video(
            chat_id=update.message.chat_id,
            video=open(video_path, 'rb'),
            supports_streaming=True
        )
    except Exception as e:
        logger.error(f"Error al enviar el video: {e}")
        await update.message.reply_text("❌ Error al enviar el video. Intenta de nuevo.")
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)  # Elimina el archivo después de enviarlo

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Descarga un video, verifica el tamaño y lo envía/sube según corresponda."""
    max_retries = 3
    retry_delay = 3  # segundos
    message = await update.message.reply_text("⏳ Iniciando descarga...")
    url = update.message.text

    try:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'noplaylist': True,
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
            'windowsfilenames': True,
            'restrictfilenames': True,
            'progress_hooks': [DownloadProgressBar(update, context)],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            temp_file = ydl.prepare_filename(info)
            
            # Renombrar con nombre seguro
            final_name = sanitize_filename(info['title'])
            final_path = os.path.join(DOWNLOAD_DIR, final_name)
            
            if os.path.exists(final_path):
                os.remove(final_path)
            
            os.rename(temp_file, final_path)

        file_size = os.path.getsize(final_path)
        if file_size <= MAX_FILE_SIZE:
            await message.edit_text("📤 Enviando video...")
            await send_video_telegram(update, context, final_path)
        else:
            await message.edit_text("📤 Subiendo a Google Drive (video muy grande)...")
            drive_link = upload_to_drive(final_path)
            await message.edit_text(
                f"🎉 ¡Video subido a Google Drive!\n\n"
                f"Enlace: {drive_link}\n\n"
                f"🎬 Más contenido como peliculas, series, anime y kdramas : https://1024terabox.com/s/1Q2xqLVhGpoukpY5uqQ-LDg"
            )
            os.remove(final_path) # Elimina despues de subir a Drive
    except yt_dlp.DownloadError as e:
        logger.error(f"Error descarga: {e}, Intento {retry_attempt + 1}/{max_retries}")
        if retry_attempt < max_retries:
            await message.edit_text(f"⚠️ Error al descargar. Reintentando en {retry_delay} segundos... (Intento {retry_attempt + 1}/{max_retries})")
            await asyncio.sleep(retry_delay)
            await download_video(update, context, retry_attempt + 1)  # Llamada recursiva para reintentar
        else:
            await message.edit_text("❌ Error: URL inválida o video no disponible después de varios intentos.")
    except Exception as e:
        logger.error(f"Error crítico: {e}")
        await message.edit_text("⚠️ Error interno. Contacta al soporte")
    finally:
        if 'final_path' in locals() and os.path.exists(final_path):
            os.remove(final_path)

def main() -> None:
    application = ApplicationBuilder()\
        .token(TOKEN)\
        .read_timeout(1200)\
        .write_timeout(1200)\
        .build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    application.add_error_handler(lambda u, c: logger.error(c.error))

    application.run_polling()

if __name__ == '__main__':
    main()
