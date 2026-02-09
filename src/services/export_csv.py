"""CSV export for tax filing data preparation."""
from __future__ import annotations

import csv
from pathlib import Path

from src.models.expense import Expense
from src.models.income import Income
from src.models.tax import TaxSummary


def export_tax_summary_csv(summary: TaxSummary, path: Path) -> None:
    """Export a yearly tax summary to CSV.

    Format designed for easy reference during manual 確定申告 filing.
    Uses utf-8-sig encoding (BOM) for Excel compatibility.
    """
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["確定申告 データ準備", f"{summary.year}年"])
        writer.writerow([])
        writer.writerow(["項目 (Item)", "金額 (Amount ¥)"])
        writer.writerow(["収入合計 (Gross Income)", f"{summary.gross_income:,}"])
        writer.writerow(["経費合計 (Total Expenses)", f"{summary.total_expenses:,}"])
        writer.writerow(["差引所得 (Net Income)", f"{summary.net_income:,}"])
        writer.writerow([])
        writer.writerow(["経費内訳 (Expense Breakdown)"])
        writer.writerow(["カテゴリ (Category)", "金額 (Amount ¥)"])
        for item in summary.expense_breakdown:
            writer.writerow([item.category_label, f"{item.total:,}"])


def export_income_csv(incomes: list[Income], path: Path) -> None:
    """Export income entries to CSV."""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "日付 (Date)",
            "金額 (Amount ¥)",
            "クライアント (Client)",
            "業務種別 (Job Type)",
            "備考 (Notes)",
        ])
        for inc in sorted(incomes, key=lambda x: x.income_date):
            writer.writerow([
                inc.income_date.isoformat(),
                inc.amount,
                inc.client,
                inc.job_type.value,
                inc.notes,
            ])


def export_expenses_csv(expenses: list[Expense], path: Path) -> None:
    """Export expense entries to CSV."""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "日付 (Date)",
            "金額 (Amount ¥)",
            "カテゴリ (Category)",
            "支払方法 (Payment Method)",
            "繰返 (Recurrence)",
            "備考 (Notes)",
        ])
        for exp in sorted(expenses, key=lambda x: x.expense_date):
            writer.writerow([
                exp.expense_date.isoformat(),
                exp.amount,
                exp.category.value,
                exp.payment_method.value,
                exp.recurrence.value,
                exp.notes,
            ])
