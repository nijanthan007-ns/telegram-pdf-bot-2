import logging
import os
import fitz  # PyMuPDF
import json
from googletrans import Translator
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Bot token
TOKEN = "7896691332:AAE2mQTYYtFuwR13_xD4G4mAjqDU4GmhQOI"

# Logging
logging.basicConfig(level=logging.INFO)

# File path to save PDF memory
PDF_DB_PATH = "pdf_data.json"
translator = Translator()

# Load saved data
if os.path.exists(PDF_DB_PATH):
    with open(PDF_DB_PATH, "r") as f:
        pdf_data = json.load(f)
else:
    pdf_data = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 Hi! Use /upload to send me a PDF.\n"
        "Use /list to see uploaded PDFs.\n"
        "Then just ask your questions.\n\n"
        "👋 வணக்கம்! /upload கமாண்டைப் பயன்படுத்தி PDF அனுப்பவும்.\n"
        "/list மூலம் பதிவேற்றிய PDF-களை பார்வையிடவும்.\n"
        "பின்னர் கேள்விகளை கேட்கலாம்."
    )
    await update.message.reply_text(msg)

# /upload
async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📄 PDF அனுப்பவும். Please upload your PDF now.")

# Handle uploaded PDF
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global pdf_data
    doc = update.message.document
    if doc.mime_type != 'application/pdf':
        await update.message.reply_text("❌ Please upload a valid PDF file.")
        return

    file_id = doc.file_id
    file_name = doc.file_name or f"{doc.file_unique_id}.pdf"
    file_path = f"/tmp/{file_name}"

    new_file = await doc.get_file()
    await new_file.download_to_drive(file_path)

    pdf_text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            pdf_text += page.get_text()

    pdf_data[file_name] = {
        "file_id": file_id,
        "text": pdf_text
    }

    with open(PDF_DB_PATH, "w") as f:
        json.dump(pdf_data, f)

    await update.message.reply_text(f"✅ PDF '{file_name}' uploaded and saved!")

# /list
async def list_pdfs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not pdf_data:
        await update.message.reply_text("📭 No PDFs uploaded yet.")
        return
    msg = "📚 Uploaded PDFs:\n" + "\n".join(f"- {name}" for name in pdf_data.keys())
    await update.message.reply_text(msg)

# Text question handler
async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not pdf_data:
        await update.message.reply_text("📭 No PDFs uploaded. Please use /upload first.")
        return

    question = update.message.text

    # Detect if Tamil
    if any(char in question for char in 'அஆஇஈஉஊஎஏஐஒஓகஙசஜஞடணதநபமயரலவளழறன'):
        translated = translator.translate(question, src='ta', dest='en').text
        original_lang = 'ta'
    else:
        translated = question
        original_lang = 'en'

    combined_text = " ".join(v["text"] for v in pdf_data.values())

    answer = ""
    for sentence in combined_text.split('.'):
        if all(word.lower() in sentence.lower() for word in translated.split()):
            answer += sentence.strip() + ". "
    if answer:
        if original_lang == 'ta':
            answer = translator.translate(answer, src='en', dest='ta').text
        await update.message.reply_text("📖:\n" + answer.strip())
        return

    # Wikipedia fallback
    import requests
    search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{translated.replace(' ', '_')}"
    response = requests.get(search_url)
    if response.status_code == 200:
        summary = response.json().get("extract", "")
        if summary:
            if original_lang == 'ta':
                summary = translator.translate(summary, src='en', dest='ta').text
            await update.message.reply_text("🌐:\n" + summary)
            return

    await update.message.reply_text("❓ Sorry, I couldn't find the answer.")

# Run bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("upload", upload))
    app.add_handler(CommandHandler("list", list_pdfs))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), answer_question))
    app.run_polling()
