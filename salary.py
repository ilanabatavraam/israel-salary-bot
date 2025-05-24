# salary.py
from config import INCOME_TAX_BRACKETS, NATIONAL_INSURANCE_THRESHOLDS, PENSION_RATE, CREDIT_POINT_VALUE_MONTHLY

def calculate_income_tax(gross):
    tax = 0
    previous_limit = 0
    for limit, rate in INCOME_TAX_BRACKETS:
        if gross > previous_limit:
            taxable = min(gross, limit) - previous_limit
            tax += taxable * rate
            previous_limit = limit
        else:
            break
    return tax

def calculate_national_insurance(gross):
    insurance = 0
    previous_limit = 0
    for limit, rate in NATIONAL_INSURANCE_THRESHOLDS:
        if gross > previous_limit:
            taxable = min(gross, limit) - previous_limit
            insurance += taxable * rate
            previous_limit = limit
        else:
            break
    return insurance

def calculate_salary(hours, hourly_rate, bonus, credit_points=0):
    gross = hours * hourly_rate + bonus
    pension = gross * PENSION_RATE
    insurance = calculate_national_insurance(gross)
    income_tax = calculate_income_tax(gross)

    # Apply credit point discount
    tax_discount = credit_points * CREDIT_POINT_VALUE_MONTHLY
    income_tax = max(0, income_tax - tax_discount)

    net = gross - (pension + insurance + income_tax)
    return {
        "gross": round(gross, 2),
        "net": round(net, 2),
        "income_tax": round(income_tax, 2),
        "pension": round(pension, 2),
        "insurance": round(insurance, 2),
        "tax_discount": round(tax_discount, 2)
    }
