# config.py

BOT_TOKEN = "8187305990:AAH_h6t5H7VK8WMhlhXTRx2j-YB4JqT6vHY"

# These rates reflect Israeli rules
# (approximate for 2024/2025 — update as needed)
INCOME_TAX_BRACKETS = [
    (6790, 0.10),
    (9730, 0.14),
    (15620, 0.20),
    (21710, 0.31),
    (45180, 0.35),
    (58920, 0.47),
    (float('inf'), 0.50),
]

NATIONAL_INSURANCE_THRESHOLDS = [
    (7122, 0.031),
    (float('inf'), 0.12)
]

PENSION_RATE = 0.06

# Each Nekudat Zikui (credit point) reduces annual tax by approx. 2,796 NIS
CREDIT_POINT_VALUE_MONTHLY = 233.00
