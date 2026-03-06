import os
import google.generativeai as genai
import io
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters
from PIL import Image
import pdfplumber
import docx

# قراءة التوكنات من Railway Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# تشغيل Gemini
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")

memory = {}

# رسالة البداية
async def start(update, context):
    await update.message.reply_text(
        "🤖 بوت ذكاء اصطناعي\n\n"
        "يمكنك:\n"
        "📝 كتابة سؤال\n"
        "🖼 ارسال صورة لتحليلها\n"
        "📄 ارسال PDF او Word لتحليله\n\n"
        "/reset لمسح المحادثة"
    )

# مسح الذاكرة
async def reset(update, context):
    memory[update.message.chat_id] = []
    await update.message.reply_text("تم مسح الذاكرة")

# الرد على الرسائل
async def reply(update, context):

    user_id = update.message.chat_id
    text = update.message.text

    await update.message.reply_text("🤖 جاري التفكير...")

    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append(text)

    prompt = " ".join(memory[user_id][-5:])

    try:

        response = model.generate_content(prompt)

        answer = response.text

    except Exception as e:

        answer = f"خطأ:\n{e}"

    await update.message.reply_text(answer)

# تحليل الصور
async def analyze_image(update, context):

    await update.message.reply_text("🧠 تحليل الصورة...")

    photo = update.message.photo[-1]

    file = await context.bot.get_file(photo.file_id)

    image_bytes = await file.download_as_bytearray()

    img = Image.open(io.BytesIO(image_bytes))

    try:

        response = model.generate_content(["اشرح هذه الصورة", img])

        answer = response.text

    except Exception as e:

        answer = f"خطأ:\n{e}"

    await update.message.reply_text(answer)

# قراءة الملفات
async def read_document(update, context):

    file = await context.bot.get_file(update.message.document.file_id)

    file_bytes = await file.download_as_bytearray()

    name = update.message.document.file_name

    text = ""

    if name.endswith(".pdf"):

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:

            for page in pdf.pages:

                if page.extract_text():

                    text += page.extract_text()

    elif name.endswith(".docx"):

        doc = docx.Document(io.BytesIO(file_bytes))

        for para in doc.paragraphs:

            text += para.text

    if text == "":

        await update.message.reply_text("لم استطع قراءة الملف")

        return

    try:

        response = model.generate_content("لخص النص التالي:\n" + text[:4000])

        answer = response.text

    except Exception as e:

        answer = f"خطأ:\n{e}"

    await update.message.reply_text(answer)

# تشغيل البوت
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reset", reset))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
app.add_handler(MessageHandler(filters.PHOTO, analyze_image))
app.add_handler(MessageHandler(filters.Document.ALL, read_document))

print("GEMINI AI BOT RUNNING")

app.run_polling()
