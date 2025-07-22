import os
import fitz  # PyMuPDF
import logging
from telegram import Update, Document
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# Replace with your actual Telegram bot token
BOT_TOKEN = "7896691332:AAE2mQTYYtFuwR13_xD4G4mAjqDU4GmhQOI"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Dictionary to hold user PDFs in memory
user_pdfs = {}

# Extract text from PDF
def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I'm a simple PDF Question Answering bot.\n"
        "Upload a PDF using /upload command or send a document directly.\n"
        "Then ask your question!"
    )

# Upload command (reminder)
async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please upload a PDF file.")

# When a user uploads a document
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document: Document = update.message.document
    if document.mime_type != "application/pdf":
        await update.message.reply_text("Only PDF files are supported.")
        return

    file = await document.get_file()
    user_id = update.message.from_user.id
    file_path = f"{user_id}.pdf"
    await file.download_to_drive(file_path)

    pdf_text = extract_text_from_pdf(file_path)
    user_pdfs[user_id] = pdf_text
    os.remove(file_path)

    await update.message.reply_text("PDF uploaded and processed. You can now ask questions!")

# Handle user questions
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    question = update.message.text

    if user_id not in user_pdfs:
        await update.message.reply_text("Please upload a PDF first using /upload.")
        return

    # Naive matching (just checks if question keywords exist in PDF)
    pdf_text = user_pdfs[user_id]
    matches = [line.strip() for line in pdf_text.split('\n') if any(q in line.lower() for q in question.lower().split())]

    if matches:
        answer = "\n".join(matches[:5])
        await update.message.reply_text(f"From PDF:\n{answer}")
    else:
        await update.message.reply_text("Couldn't find relevant info in the PDF.")

# Main setup
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("upload", upload))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
