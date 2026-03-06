import os
import requests
import io
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters
from PIL import Image
import pdfplumber
import docx

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

memory = {}

async def start(update, context):

    await update.message.reply_text(
        "🤖 بوت ذكاء اصطناعي\n\n"
        "يمكنك:\n"
        "📝 كتابة سؤال\n"
        "🖼 ارسال صورة لتحليلها\n"
        "📄 ارسال PDF او Word لتحليله\n\n"
        "/reset لمسح المحادثة"
    )

async def reset(update, context):

    memory[update.message.chat_id] = []

    await update.message.reply_text("تم مسح الذاكرة")

async def ask_ai(prompt):

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "mistralai/mistral-7b-instruct",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    )

    return response.json()["choices"][0]["message"]["content"]

async def reply(update, context):

    user_id = update.message.chat_id
    text = update.message.text

    await update.message.reply_text("🤖 جاري التفكير...")

    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append(text)

    prompt = " ".join(memory[user_id][-5:])

    try:

        answer = await ask_ai(prompt)

    except Exception as e:

        answer = str(e)

    await update.message.reply_text(answer)

async def analyze_image(update, context):

    await update.message.reply_text("🧠 تحليل الصورة...")

    photo = update.message.photo[-1]

    file = await context.bot.get_file(photo.file_id)

    image_bytes = await file.download_as_bytearray()

    img = Image.open(io.BytesIO(image_bytes))

    try:

        answer = await ask_ai(
            "اشرح هذه الصورة بالتفصيل"
        )

    except Exception as e:

        answer = str(e)

    await update.message.reply_text(answer)

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

        answer = await ask_ai(
            "لخص النص التالي:\n" + text[:4000]
        )

    except Exception as e:

        answer = str(e)

    await update.message.reply_text(answer)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reset", reset))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
app.add_handler(MessageHandler(filters.PHOTO, analyze_image))
app.add_handler(MessageHandler(filters.Document.ALL, read_document))

print("AI BOT RUNNING")

app.run_polling()
