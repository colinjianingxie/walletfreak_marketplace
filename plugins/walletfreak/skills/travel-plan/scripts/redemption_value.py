#!/usr/bin/env python3
"""Calculate a comparable redemption value. No network or saved account data."""
import argparse
from decimal import Decimal, InvalidOperation
import json
import re


def redemption_value(cash_total, award_cash, points, cash_currency, award_currency):
    if not isinstance(cash_currency, str) or not re.fullmatch(r"[A-Z]{3}", cash_currency):
        raise ValueError("Use an explicit three-letter cash currency.")
    if cash_currency != award_currency:
        raise ValueError("Currencies differ: disclose a sourced conversion before calculating.")
    try:
        cash, charges, spent = (Decimal(str(v)) for v in (cash_total, award_cash, points))
    except InvalidOperation as error:
        raise ValueError("All mandatory cash charges and points must be known numbers.") from error
    if not all(v.is_finite() for v in (cash, charges, spent)):
        raise ValueError("Amounts must be finite.")
    if cash < 0 or charges < 0 or spent <= 0 or spent != spent.to_integral_value():
        raise ValueError("Cash amounts must be nonnegative and points a positive integer.")
    value = (cash - charges) / spent
    return {"currency": cash_currency, "per_point": str(value), "cents_per_point": str(value * 100)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cash_total")
    parser.add_argument("award_cash")
    parser.add_argument("points")
    parser.add_argument("--cash-currency", required=True)
    parser.add_argument("--award-currency", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(redemption_value(**vars(args))))
    except ValueError as error:
        parser.error(str(error))
