# bot.py
import asyncio
import nest_asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers import (
    start_command, menu_command, handle_button,
    handle_text_input, language_command
)
from db import init_db, get_all_users
from monthly_report import generate_monthly_pdf
from telegram import InputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import os

nest_asyncio.apply()

# Replace this with your actual bot token
TOKEN = ""

# Scheduled task to send reports
async def send_monthly_reports(application):
    now = datetime.now()
    last_month = now.replace(day=1) - timedelta(days=1)
    year = last_month.year
    month = last_month.month
    user_ids = await get_all_users()
    for user_id in user_ids:
        try:
            pdf_path = await generate_monthly_pdf(user_id, year, month)
            await application.bot.send_document(chat_id=user_id, document=InputFile(pdf_path))
            os.remove(pdf_path)
        except Exception as e:
            print(f"Failed to send report to {user_id}: {e}")

# Main entrypoint
async def main():
    await init_db()
    app = Application.builder().token(TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("menu", menu_command))
    # app.add_handler(CommandHandler("summary", monthly_summary))
    app.add_handler(CommandHandler("language", language_command))

    # Register message handler (for user text input)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    # Register callback handler for buttons
    app.add_handler(CallbackQueryHandler(handle_button))

    # Schedule job: send PDF reports monthly
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(send_monthly_reports(app)), "cron", day=1, hour=9)
    scheduler.start()

    print("✅ Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
