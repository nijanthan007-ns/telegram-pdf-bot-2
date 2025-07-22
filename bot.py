import os
import fitz  # PyMuPDF
import logging
import requests
from io import BytesIO
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from deep_translator import GoogleTranslator

BOT_TOKEN = "7896691332:AAE2mQTYYtFuwR13_xD4G4mAjqDU4GmhQOI"
PDF_MEMORY = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Welcome to PDF Bot!\n\n"
        "Commands:\n"
        "/upload - Upload a new PDF\n"
        "/list - List saved PDFs\n\n"
        "💬 Just ask a question in English or Tamil."
    )

async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📎 Please send me a PDF file to upload.")

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document or not update.message.document.file_name.endswith('.pdf'):
        await update.message.reply_text("❌ Please send a valid PDF file.")
        return

    file_id = update.message.document.file_id
    file_name = update.message.document.file_name

    new_file = await context.bot.get_file(file_id)
    file_bytes = await new_file.download_as_bytearray()

    pdf_text = extract_text_from_pdf(file_bytes)
    PDF_MEMORY[file_name] = {"text": pdf_text, "file_id": file_id}

    await update.message.reply_text(f"✅ PDF '{file_name}' saved!")

def extract_text_from_pdf(file_bytes):
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

async def list_pdfs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not PDF_MEMORY:
        await update.message.reply_text("📂 No PDFs uploaded yet.")
        return

    msg = "📄 Stored PDFs:\n\n"
    for name in PDF_MEMORY:
        msg += f"• {name}\n"
    await update.message.reply_text(msg)

def search_pdf(query, pdf_text):
    query = query.lower()
    for line in pdf_text.split("\n"):
        if query in line.lower():
            return line
    return None

def detect_language(text):
    tamil_chars = [c for c in text if '\u0B80' <= c <= '\u0BFF']
    return 'ta' if len(tamil_chars) > 3 else 'en'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    original_lang = detect_language(user_input)

    if original_lang == 'ta':
        user_input = GoogleTranslator(source='ta', target='en').translate(user_input)

    for pdf_data in PDF_MEMORY.values():
        answer = search_pdf(user_input, pdf_data["text"])
        if answer:
            if original_lang == 'ta':
                answer = GoogleTranslator(source='en', target='ta').translate(answer)
            await update.message.reply_text("📖:\n" + answer.strip())
            return

    # Fallback to Wikipedia
    try:
        wiki_summary = get_summary_from_wikipedia(user_input)
        if original_lang == 'ta':
            wiki_summary = GoogleTranslator(source='en', target='ta').translate(wiki_summary)
        await update.message.reply_text("🌐 From Wikipedia:\n" + wiki_summary)
    except:
        await update.message.reply_text("❌ Sorry, no answer found.")

def get_summary_from_wikipedia(query):
    resp = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}")
    if resp.status_code == 200:
        return resp.json().get("extract", "No summary found.")
    return "No info found."

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("upload", upload))
    app.add_handler(CommandHandler("list", list_pdfs))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 Bot started...")
    app.run_polling()
