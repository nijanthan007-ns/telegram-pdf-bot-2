
import logging
import os
import fitz  # PyMuPDF
import requests
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Bot token
TOKEN = "7896691332:AAE2mQTYYtFuwR13_xD4G4mAjqDU4GmhQOI"

# Setup logging
logging.basicConfig(level=logging.INFO)

# Store PDF content
PDF_TEXT = ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Send me a PDF using /upload and then ask questions about it.")

async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please upload the PDF file now.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global PDF_TEXT
    doc = update.message.document
    if doc.mime_type != 'application/pdf':
        await update.message.reply_text("Please upload a valid PDF file.")
        return

    file = await doc.get_file()
    file_path = f"{doc.file_unique_id}.pdf"
    await file.download_to_drive(file_path)

    # Read PDF
    with fitz.open(file_path) as pdf:
        PDF_TEXT = ""
        for page in pdf:
            PDF_TEXT += page.get_text()

    os.remove(file_path)
    await update.message.reply_text("PDF uploaded and processed. Ask me anything from it!")

async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global PDF_TEXT
    question = update.message.text

    if PDF_TEXT.strip():
        # Very simple logic: check if question words are in PDF
        answer = ""
        for sentence in PDF_TEXT.split('.'):
            if all(word.lower() in sentence.lower() for word in question.split()):
                answer += sentence.strip() + ". "
        if answer:
            await update.message.reply_text("From PDF:
" + answer.strip())
            return

    # Wikipedia fallback
    search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{question.replace(' ', '_')}"
    response = requests.get(search_url)
    if response.status_code == 200:
        data = response.json()
        summary = data.get("extract")
        if summary:
            await update.message.reply_text("From Internet:
" + summary)
            return

    await update.message.reply_text("Sorry, I couldn't find the answer.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("upload", upload))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), answer_question))
    app.run_polling()
