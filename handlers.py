# handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes
from db import (
    register_user, update_rate, update_bonus,
    update_credit_points, update_language,
    get_user_language, start_session, stop_session,
    get_sessions_by_month, save_manual_session,
    get_user_active_months, get_sessions_by_day
)
from monthly_report import generate_monthly_summary, generate_monthly_pdf
from datetime import datetime, timedelta
import dateutil.parser
import re
import logging
import os

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)

logger = logging.getLogger(__name__)

# Language helper
async def get_texts(user_id):
    lang = await get_user_language(user_id)
    return {
        'rate_prompt': {
            'en': "💬 Please enter your hourly rate (e.g. 45):",
            'ru': "💬 Введите вашу почасовую ставку (например, 45):"
        },
        'bonus_prompt': {
            'en': "💬 Please enter your transport bonus (e.g. 300):",
            'ru': "💬 Введите ваш транспортный бонус (например, 300):"
        },
        'credits_prompt': {
            'en': "💬 Please enter your credit points (e.g. 2.25):",
            'ru': "💬 Введите количество некудот зекуй (например, 2.25):"
        },
        'invalid_number': {
            'en': "❌ Please enter a valid number.",
            'ru': "❌ Пожалуйста, введите корректное число."
        },
        'rate_set': {
            'en': "✅ Hourly rate set to ₪{:.2f}",
            'ru': "✅ Почасовая ставка установлена: ₪{:.2f}"
        },
        'bonus_set': {
            'en': "✅ Transport bonus set to ₪{:.2f}",
            'ru': "✅ Транспортный бонус установлен: ₪{:.2f}"
        },
        'credits_set': {
            'en': "✅ Credit points set to {:.2f}",
            'ru': "✅ Некудот зекуй установлены: {:.2f}"
        },
        'lang_prompt': {
            'en': "🌍 Choose your preferred language:",
            'ru': "🌍 Выберите язык интерфейса:"
        },
        'lang_set': {
            'en': "Language set to English.",
            'ru': "Язык установлен: Русский."
        },
        'work_started': {
            'en': "✅ Work started.",
            'ru': "✅ Работа началась."
        },
        'work_stopped': {
            'en': "🛑 Work stopped.",
            'ru': "🛑 Работа завершена."
        },
        'today_worked': {
            'en': "🕒 You worked {:.2f} hours today.",
            'ru': "🕒 Сегодня вы отработали {:.2f} часов."
        },
        'fix_sessions': {
            'en': "🛠 Fix Sessions",
            'ru': "🛠 Исправить дни"
        },
        'add_session_prompt': {
            'en': "✏️ Send your session in format: 2025-05-24 09:00 - 17:00",
            'ru': "✏️ Введите сессию: 2025-05-24 09:00 - 17:00"
        },
        'session_saved': {
            'en': "✅ Session saved.",
            'ru': "✅ Сессия сохранена."
        },
        'invalid_format': {
            'en': "❌ Invalid format. Use: YYYY-MM-DD HH:MM - HH:MM",
            'ru': "❌ Неверный формат. Пример: 2025-05-24 09:00 - 17:00"
        },
        'select_month': {
            'en': "📅 Select a month:",
            'ru': "📅 Выберите месяц:"
        },
        'pdf_report_sent': {
            'en': "📄 PDF report sent!",
            'ru': "📄 PDF отчет отправлен!"
        },
        'select_day_prompt': {
            'en': "📅 Enter a date (YYYY-MM-DD) to view or add work:",
            'ru': "📅 Введите дату (ГГГГ-ММ-ДД) чтобы просмотреть или добавить работу:"
        },
        'existing_sessions': {
            'en': "📋 Sessions for {date}:",
            'ru': "📋 Сессии на {date}:"
        },
        'add_range_prompt': {
            'en': "✏️ Now enter time range (HH:MM - HH:MM):",
            'ru': "✏️ Введите диапазон времени (ЧЧ:ММ - ЧЧ:ММ):"
        },
        'invalid_date': {
            'en': "❌ Invalid date. Use YYYY-MM-DD.",
            'ru': "❌ Неверная дата. Используйте ГГГГ-ММ-ДД."
        }
    }, lang

# Show main menu
async def show_main_menu(update_or_query, context):
    user_id = update_or_query.effective_user.id if hasattr(update_or_query, 'effective_user') else update_or_query.from_user.id
    lang = await get_user_language(user_id)

    texts = {
        'en': {
            'choose': "Please choose an action:",
            'set_rate': "Rate",
            'set_credits': "Credits",
            'set_bonus': "Bonus",
            'start': "Start",
            'stop': "Stop",
            'summary': "Summary",
            'language': "🌐 Language",
            'fix': "🛠 Fix Sessions",
            'edit': "🗓 Edit/Add Past Day"
        },
        'ru': {
            'choose': "Выберите действие:",
            'set_rate': "Ставка",
            'set_credits': "Некудот зекуй",
            'set_bonus': "Бонус",
            'start': "Начать",
            'stop': "Стоп",
            'summary': "Отчет",
            'language': "🌐 Язык",
            'fix': "🛠 Исправить дни",
            'edit': "🗓 Добавить день"
        }
    }
    t = texts[lang]
    keyboard = [
        [InlineKeyboardButton(t['set_rate'], callback_data="set_rate"),
         InlineKeyboardButton(t['set_credits'], callback_data="set_credits")],
        [InlineKeyboardButton(t['set_bonus'], callback_data="set_bonus")],
        [InlineKeyboardButton(t['start'], callback_data="start_work"),
         InlineKeyboardButton(t['stop'], callback_data="stop_work")],
        [InlineKeyboardButton(t['summary'], callback_data="summary"),
         InlineKeyboardButton(t['language'], callback_data="language")],
        [InlineKeyboardButton(t['fix'], callback_data="fix_sessions")],
        [InlineKeyboardButton(t['edit'], callback_data="edit_past")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if hasattr(update_or_query, "message") and update_or_query.message:
        await update_or_query.message.reply_text(t['choose'], reply_markup=reply_markup)
    else:
        await update_or_query.edit_message_text(t['choose'], reply_markup=reply_markup)

# Start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await register_user(user_id)
    keyboard = [[InlineKeyboardButton("English", callback_data="lang_en"),
                 InlineKeyboardButton("Russian", callback_data="lang_ru")]]
    await update.message.reply_text("🌍 Please choose your preferred language:", reply_markup=InlineKeyboardMarkup(keyboard))

# Command handlers
async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages, lang = await get_texts(update.effective_user.id)
    keyboard = [[InlineKeyboardButton("English", callback_data="lang_en"),
                 InlineKeyboardButton("Russian", callback_data="lang_ru")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(messages['lang_prompt'][lang], reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(messages['lang_prompt'][lang], reply_markup=reply_markup)

# Handle plain text input
async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    messages, lang = await get_texts(user_id)
    pending = context.user_data.get("pending_input")
    text = update.message.text.strip()

    try:
        if pending == "rate":
            await update_rate(user_id, float(text))
            await update.message.reply_text(messages['rate_set'][lang].format(float(text)))
            context.user_data.pop("pending_input", None)
            await show_main_menu(update, context)
        elif pending == "bonus":
            await update_bonus(user_id, float(text))
            await update.message.reply_text(messages['bonus_set'][lang].format(float(text)))
            context.user_data.pop("pending_input", None)
            await show_main_menu(update, context)
        elif pending == "credits":
            await update_credit_points(user_id, float(text))
            await update.message.reply_text(messages['credits_set'][lang].format(float(text)))
            context.user_data.pop("pending_input", None)
            await show_main_menu(update, context)
        elif pending == "manual_session":
            match = re.match(r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})", text)
            if match:
                date_str, start_str, end_str = match.groups()
                start_dt = datetime.fromisoformat(f"{date_str}T{start_str}")
                end_dt = datetime.fromisoformat(f"{date_str}T{end_str}")
                if end_dt > start_dt:
                    await save_manual_session(user_id, start_dt.isoformat(), end_dt.isoformat())
                    await update.message.reply_text(messages['session_saved'][lang])
                else:
                    await update.message.reply_text(messages['invalid_format'][lang])
            else:
                await update.message.reply_text(messages['invalid_format'][lang])
            context.user_data.pop("pending_input", None)
            await show_main_menu(update, context)
        elif pending == "select_day":
            try:
                day = datetime.strptime(text, "%Y-%m-%d").date()
                context.user_data['selected_day'] = day.isoformat()
                sessions = await get_sessions_by_day(user_id, day.isoformat())
                if sessions:
                    reply = messages['existing_sessions'][lang].format(date=day.isoformat()) + "\n"
                    for start, end in sessions:
                        st = dateutil.parser.isoparse(start).strftime('%H:%M')
                        et = dateutil.parser.isoparse(end).strftime('%H:%M')
                        reply += f"- {st} - {et}\n"
                    await update.message.reply_text(reply)
                context.user_data["pending_input"] = "add_time_range"
                await update.message.reply_text(messages['add_range_prompt'][lang])
            except ValueError:
                await update.message.reply_text(messages['invalid_date'][lang])
        elif pending == "add_time_range":
            if 'selected_day' in context.user_data:
                match = re.match(r"(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})", text)
                if match:
                    start_str, end_str = match.groups()
                    date_str = context.user_data['selected_day']
                    start_dt = datetime.fromisoformat(f"{date_str}T{start_str}")
                    end_dt = datetime.fromisoformat(f"{date_str}T{end_str}")
                    if end_dt > start_dt:
                        await save_manual_session(user_id, start_dt.isoformat(), end_dt.isoformat())
                        await update.message.reply_text(messages['session_saved'][lang])
                        context.user_data.pop("pending_input", None)
                        context.user_data.pop("selected_day", None)
                        await show_main_menu(update, context)
                    else:
                        await update.message.reply_text(messages['invalid_format'][lang])
                else:
                    await update.message.reply_text(messages['invalid_format'][lang])
    except ValueError:
        await update.message.reply_text(messages['invalid_number'][lang])


# Callback handler
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    messages, lang = await get_texts(user_id)

    if query.data == "start_work":
        await start_session(user_id, datetime.now().isoformat())
        await query.answer()
        await query.edit_message_text(messages['work_started'][lang])
    elif query.data == "stop_work":
        await stop_session(user_id, datetime.now().isoformat())
        await query.answer()
        now = datetime.now()
        total = 0
        for start, end in await get_sessions_by_month(user_id, now.year, now.month):
            st, et = dateutil.parser.isoparse(start), dateutil.parser.isoparse(end)
            if st.date() == now.date():
                total += (et - st).total_seconds() / 3600
        await query.edit_message_text(messages['today_worked'][lang].format(total))
    elif query.data == "set_rate":
        context.user_data["pending_input"] = "rate"
        await query.answer()
        await query.edit_message_text(messages['rate_prompt'][lang])
    elif query.data == "set_bonus":
        context.user_data["pending_input"] = "bonus"
        await query.answer()
        await query.edit_message_text(messages['bonus_prompt'][lang])
    elif query.data == "set_credits":
        context.user_data["pending_input"] = "credits"
        await query.answer()
        await query.edit_message_text(messages['credits_prompt'][lang])
    elif query.data == "summary":
        await query.answer()
        now = datetime.now()
        summary = await generate_monthly_summary(user_id, now.year, now.month)
        await query.edit_message_text(summary)
    elif query.data == "fix_sessions":
        context.user_data["pending_input"] = "manual_session"
        await query.answer()
        await query.edit_message_text(messages['add_session_prompt'][lang])
    elif query.data == "language":
        await language_command(update, context)
    elif query.data == "lang_en":
        await update_language(user_id, "en")
        await query.answer()
        await query.edit_message_text("Language set to English.")
    elif query.data == "lang_ru":
        await update_language(user_id, "ru")
        await query.answer()
        await query.edit_message_text("Язык установлен: Русский.")
    elif query.data == "select_month":
        await query.answer()
        months = await get_user_active_months(user_id)
        buttons = [InlineKeyboardButton(f"🗓 {y}-{m:02d}", callback_data=f"month_{y}-{m:02d}") for y, m in months]
        markup = InlineKeyboardMarkup([buttons[i:i+3] for i in range(0, len(buttons), 3)])
        await query.edit_message_text(messages['select_month'][lang], reply_markup=markup)
    elif query.data.startswith("month_"):
        await query.answer()
        y, m = map(int, query.data.split("_")[1].split("-"))
        summary = await generate_monthly_summary(user_id, y, m)
        pdf = await generate_monthly_pdf(user_id, y, m)
        await query.edit_message_text(summary)
        await context.bot.send_document(chat_id=query.message.chat_id, document=InputFile(pdf))
        await context.bot.send_message(chat_id=query.message.chat_id, text=messages['pdf_report_sent'][lang])
        os.remove(pdf)
    elif query.data == "edit_past":
        context.user_data["pending_input"] = "select_day"
        await query.answer()
        await query.edit_message_text(messages['select_day_prompt'][lang])
    if context.user_data.get("pending_input") is None:
        await show_main_menu(query, context)


