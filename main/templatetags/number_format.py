from django import template

register = template.Library()


@register.filter
def miles(value):
    """
    Formatea un número con separador de miles usando punto (formato español/latino).
    Ejemplo: 1234567 -> "1.234.567"
    """
    try:
        # Convertir a entero para quitar decimales
        num = int(float(value))
        # Formatear con separador de miles
        formatted = "{:,}".format(num).replace(",", ".")
        return formatted
    except (ValueError, TypeError):
        return value


@register.filter
def miles_usd(value):
    """
    Formatea un valor USD con separador de miles y 2 decimales.
    Ejemplo: 1234567.89 -> "$1.234.567,89"
    """
    try:
        num = float(value)
        # Formatear con 2 decimales
        formatted = "{:,.2f}".format(num)
        # Cambiar formato: coma -> punto para miles, punto -> coma para decimales
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"${formatted}"
    except (ValueError, TypeError):
        return value
