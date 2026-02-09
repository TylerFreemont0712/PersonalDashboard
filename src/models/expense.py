from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


class ExpenseCategory(enum.Enum):
    RENT = "rent"
    UTILITIES = "utilities"
    SUBSCRIPTIONS = "subscriptions"
    GROCERIES = "groceries"
    TRANSPORTATION = "transportation"
    INSURANCE = "insurance"
    MEDICAL = "medical"
    DINING = "dining"
    ENTERTAINMENT = "entertainment"
    EDUCATION = "education"
    OFFICE_SUPPLIES = "office_supplies"
    COMMUNICATION = "communication"
    TAX_PAYMENT = "tax_payment"
    PENSION = "pension"
    OTHER = "other"


class PaymentMethod(enum.Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    CONVENIENCE_STORE = "convenience_store"
    DIRECT_DEBIT = "direct_debit"
    OTHER = "other"


class RecurrenceType(enum.Enum):
    NONE = "none"
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass
class Expense:
    amount: int  # Stored in yen (integer, no decimals needed)
    category: ExpenseCategory
    expense_date: date
    payment_method: PaymentMethod
    recurrence: RecurrenceType = RecurrenceType.NONE
    notes: str = ""
    id: Optional[int] = field(default=None)

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Expense amount must not be negative")

    @property
    def is_recurring(self) -> bool:
        return self.recurrence != RecurrenceType.NONE

    @property
    def category_label(self) -> str:
        """Human-readable category label."""
        labels = {
            ExpenseCategory.RENT: "家賃 (Rent)",
            ExpenseCategory.UTILITIES: "光熱費 (Utilities)",
            ExpenseCategory.SUBSCRIPTIONS: "サブスク (Subscriptions)",
            ExpenseCategory.GROCERIES: "食料品 (Groceries)",
            ExpenseCategory.TRANSPORTATION: "交通費 (Transportation)",
            ExpenseCategory.INSURANCE: "保険 (Insurance)",
            ExpenseCategory.MEDICAL: "医療費 (Medical)",
            ExpenseCategory.DINING: "外食 (Dining)",
            ExpenseCategory.ENTERTAINMENT: "娯楽 (Entertainment)",
            ExpenseCategory.EDUCATION: "教育 (Education)",
            ExpenseCategory.OFFICE_SUPPLIES: "事務用品 (Office Supplies)",
            ExpenseCategory.COMMUNICATION: "通信費 (Communication)",
            ExpenseCategory.TAX_PAYMENT: "税金 (Tax Payment)",
            ExpenseCategory.PENSION: "年金 (Pension)",
            ExpenseCategory.OTHER: "その他 (Other)",
        }
        return labels[self.category]
