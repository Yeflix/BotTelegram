import telebot
import os
import yt_dlp

# Inicializa el bot con el token
bot = telebot.TeleBot("7508285061:AAGH_qh4-2tBuq-FBX-Xxkt-JbFoc1gmTk8")  # Reemplaza con tu token

# Define la ruta de salida para los audios descargados
ruta = os.path.join(os.getcwd(), "salida_audio")
if not os.path.exists(ruta):
    os.makedirs(ruta)  # Crea el directorio si no existe

@bot.message_handler(commands=["start", "help"])
def enviar(message):    
    bot.reply_to(message, "Hola, soy un bot que convierte videos de YouTube a audio. Envía el enlace del video que deseas convertir.")

@bot.message_handler(func=lambda message: True)
def descargar_audio(message):
    direccion = message.text
    mess = message.chat.id
    try:
        bot.reply_to(message, "Obteniendo información del video, espere un momento...")
        
        # Configuración de opciones para yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',  # Mejor calidad de audio
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',  # Usar FFmpeg para extraer audio
                'preferredcodec': 'mp3',  # Convertir a MP3
                'preferredquality': '192',  # Calidad de audio
                
            }],
            'outtmpl': os.path.join(ruta, '%(title)s.%(ext)s'),  # Ruta de salida
        }

        # Descarga el audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([direccion])
        
        # Envía el audio al usuario
        audio_title = os.path.join(ruta, f"{ydl.prepare_filename({'title': 'audio'})}.mp3")
        with open(audio_title, "rb") as audio_file:
            bot.send_document(mess, audio_file)

        # Opcional: Eliminar el archivo después de enviarlo
        os.remove(audio_title)
        
    except yt_dlp.utils.DownloadError:
        bot.reply_to(message, "El video no está disponible o ha ocurrido un error en la descarga.")
    except Exception as e:
        bot.reply_to(message, f"Ocurrió un error: {str(e)}")

# Inicia el polling del bot
bot.infinity_polling()