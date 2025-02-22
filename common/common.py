from settings.models import StoreSettings


def formatted_amount(amount):
    store_settings = StoreSettings.objects.first()
    """Format amount based on Store settings currency symbol with thousand separators."""
    try:
        total_price = float(amount) or 0  # Ensure the value is a number
        return f"{store_settings.currency_symbol}{total_price:,.2f}"  # Formats with Peso symbol and two decimal places
    except (ValueError, TypeError):
        return "Invalid Amount"
