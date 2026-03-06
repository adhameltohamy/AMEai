import requests
import io
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters
from PIL import Image
import pdfplumber
import docx

TELEGRAM_TOKEN = "8582844371:AAF4juSijpqKGGgYX1WA7SJHQhlLFMiDRSA"
HF_TOKEN = "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"

TEXT_API = "https://api-inference.huggingface.co/models/google/flan-t5-large"
IMAGE_ANALYSIS_API = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
IMAGE_GENERATE_API = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

memory = {}

async def start(update, context):

    await update.message.reply_text(
        "🤖 بوت ذكاء اصطناعي\n\n"
        "يمكنك:\n"
        "📝 كتابة سؤال\n"
        "🖼 ارسال صورة لتحليلها\n"
        "📄 ارسال PDF او Word لتحليله\n"
        "🎨 /image لإنشاء صورة\n\n"
        "/reset لمسح المحادثة"
    )


async def reset(update, context):

    memory[update.message.chat_id] = []

    await update.message.reply_text("تم مسح الذاكرة")


async def reply(update, context):

    user_id = update.message.chat_id
    text = update.message.text

    await update.message.reply_text("🤖 جاري التفكير...")

    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append(text)

    prompt = " ".join(memory[user_id][-3:])

    try:

        response = requests.post(
            TEXT_API,
            headers=headers,
            json={
                "inputs": prompt,
                "options": {"wait_for_model": True}
            }
        )

        data = response.json()

        if isinstance(data, list):

            answer = data[0]["generated_text"]

        else:

            answer = "حدث خطأ حاول مرة أخرى"

    except:

        answer = "❌ خطأ في الاتصال"

    await update.message.reply_text(answer)


async def analyze_image(update, context):

    await update.message.reply_text("🧠 تحليل الصورة...")

    photo = update.message.photo[-1]

    file = await context.bot.get_file(photo.file_id)

    image_bytes = await file.download_as_bytearray()

    response = requests.post(
        IMAGE_ANALYSIS_API,
        headers=headers,
        data=image_bytes
    )

    try:

        caption = response.json()[0]["generated_text"]

    except:

        caption = "لم استطع فهم الصورة"

    await update.message.reply_text(f"📷 وصف الصورة:\n{caption}")


async def generate_image(update, context):

    prompt = update.message.text.replace("/image ", "")

    await update.message.reply_text("🎨 جاري إنشاء الصورة...")

    response = requests.post(
        IMAGE_GENERATE_API,
        headers=headers,
        json={
            "inputs": prompt,
            "options": {"wait_for_model": True}
        }
    )

    image_bytes = response.content

    await update.message.reply_photo(photo=image_bytes)


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

        text = "لم استطع قراءة الملف"

    await update.message.reply_text(text[:3000])


app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(CommandHandler("image", generate_image))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
app.add_handler(MessageHandler(filters.PHOTO, analyze_image))
app.add_handler(MessageHandler(filters.Document.ALL, read_document))

print("AI BOT RUNNING")

app.run_polling()
