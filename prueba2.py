import telebot
import os
import yt_dlp

# Inicializa el bot con el token
bot = telebot.TeleBot("7380444357:AAFt7sbr8EQF8F0EGcjAb31w2MkYX2N3S3g")

# Define la ruta de salida para los videos descargados
ruta = os.path.join(os.getcwd(), "salida")
if not os.path.exists(ruta):
    os.makedirs(ruta)  # Crea el directorio si no existe

@bot.message_handler(commands=["start", "help", "iniciar", "Iniciar" , "Start"])
def enviar(message):    
    bot.reply_to(message, "Hola, soy un bot creado por Yefri. Escribe y envie /Descarga, luego de enviar el mensaje. elija el video de Youtube de su Preferencia, copie el link del video y envielo en un mensaje")

@bot.message_handler(commands=["Descargar", "descargar" , "descarga", "Descarga"])
def solicitar_direccion(message):
    bot.reply_to(message, "Ingrese la dirección del video que quiere descargar:")

@bot.message_handler(func=lambda message: True)
def descargar_video(message):
    direccion = message.text
    mess = message.chat.id
    try:
        bot.reply_to(message, "Su video está descargando, espere un momento...")
        
        # Configuración de opciones para yt-dlp
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(ruta, '%(title)s.%(ext)s'),  # Ruta de salida
            'noplaylist': True,  # No descargar listas de reproducción
        }

        # Descarga el video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([direccion])
        
        # Obtiene el nombre del archivo descargado
        video_title = ydl.prepare_filename(ydl.extract_info(direccion, download=False))
        
        # Envía el video al usuario
        with open(video_title, "rb") as video_file:
            bot.send_document(mess, video_file)

      
        # Opcional: Eliminar el archivo después de enviarlo
        os.remove(video_title)
        
    except yt_dlp.utils.DownloadError:
        bot.reply_to(message, "El video no está disponible o ha ocurrido un error en la descarga.")
    except Exception as e:
        bot.reply_to(message, f"Ocurrió un error: {str(e)}")

# Inicia el polling del bot
bot.infinity_polling()