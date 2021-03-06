import decimal

DECIMAL_QUANTIZE = decimal.Decimal('0.01')


def round_decimal(d: decimal.Decimal) -> decimal.Decimal:
    return decimal.Decimal(d).quantize(DECIMAL_QUANTIZE, decimal.ROUND_HALF_UP)
