import telebot
import yt_dlp
import os

8744352264:AAGEWNK6AcrKKatWFnPhtACY2x070buKklM
API_TOKEN = '8744352264:AAGEWNK6AcrKKatWFnPhtACY2x070buKklM'
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك! أرسل لي رابط الفيديو (يوتيوب، فيسبوك، انستجرام...) وسأقوم بتحميله لك.")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text
    bot.reply_to(message, "جاري معالجة الرابط، انتظر قليلاً... ⏳")

    # إعدادات yt-dlp
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.%(ext)s', # اسم الملف المؤقت
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # إرسال الفيديو للمستخدم
            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video, caption="تم التحميل بواسطة بوتك الخاص! ✅")
            
            # حذف الملف من السيرفر بعد الإرسال لتوفير المساحة
            os.remove(filename)

    except Exception as e:
        bot.reply_to(message, f"عذراً، حدث خطأ أثناء التحميل: {str(e)}")

print("البوت يعمل الآن...")
bot.infinity_polling()
