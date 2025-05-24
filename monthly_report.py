# monthly_report.py
from db import get_sessions_by_month, get_user_settings
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

async def generate_monthly_summary(user_id, year, month):
    sessions = await get_sessions_by_month(user_id, year, month)
    settings = await get_user_settings(user_id)

    hourly_rate = settings['hourly_rate'] or 0
    transport_bonus = settings['transport_bonus'] or 0
    credit_points = settings['credit_points'] or 0
    lang = settings.get('language', 'en')

    total_hours = 0
    for start, end in sessions:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        total_hours += (end_dt - start_dt).total_seconds() / 3600.0

    gross_salary = hourly_rate * total_hours + transport_bonus

    pension_rate = 0.06
    social_security_rate = 0.07
    credit_point_value = 235

    pension = gross_salary * pension_rate
    social = gross_salary * social_security_rate

    taxable_income = gross_salary - (credit_points * credit_point_value)
    income_tax = max(taxable_income * 0.1, 0)

    net_salary = gross_salary - pension - social - income_tax

    if lang == 'ru':
        return (
            f"📅 Отчет за {month:02d}/{year}\n"
            f"⏱ Часы: {total_hours:.2f}\n"
            f"💰 Брутто: ₪{gross_salary:.2f}\n"
            f"🧾 Налог: ₪{income_tax:.2f}\n"
            f"🏦 Пенсия: ₪{pension:.2f}\n"
            f"🛡 Соц. взнос: ₪{social:.2f}\n"
            f"💸 Нетто: ₪{net_salary:.2f}"
        )
    else:
        return (
            f"📅 Report for {month:02d}/{year}\n"
            f"⏱ Hours: {total_hours:.2f}\n"
            f"💰 Gross: ₪{gross_salary:.2f}\n"
            f"🧾 Tax: ₪{income_tax:.2f}\n"
            f"🏦 Pension: ₪{pension:.2f}\n"
            f"🛡 Social: ₪{social:.2f}\n"
            f"💸 Net: ₪{net_salary:.2f}"
        )

async def generate_monthly_pdf(user_id, year, month):
    summary = await generate_monthly_summary(user_id, year, month)
    filename = f"report_{user_id}_{year}_{month:02d}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    text = c.beginText(40, 800)
    for line in summary.splitlines():
        text.textLine(line)
    c.drawText(text)
    c.save()
    return filename
