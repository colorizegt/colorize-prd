def prepare_domain_v2(domain):
    """
    Convierte un domain con operador 'date_filter' a un domain estándar.
    Retorna una lista de tuplas/strings (formato de domain de Odoo).
    """
    if not isinstance(domain, (tuple, list)) or len(domain) != 3:
        return [tuple(domain)] if isinstance(domain, (tuple, list)) else []

    field_name = domain[0]
    operator = domain[1]
    val = domain[2]

    date_format = '%Y-%m-%d %H:%M:%S'

    current_date = datetime.now()
    current_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0)

    if operator != "date_filter":
        return [tuple(domain)]

    # Mapeo de valores a cálculos
    if val == "today":
        start = current_date
        end = current_date + timedelta(days=1)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    if val == "this_week":
        start = current_date - timedelta(days=current_date.weekday())
        end = start + timedelta(days=7)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    if val == "this_month":
        start = current_date.replace(day=1)
        end = start + relativedelta(months=1)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    if val == "this_quarter":
        start = datetime(current_date.year, ((current_date.month - 1) // 3) * 3 + 1, 1)
        end = start + relativedelta(months=3)
        return ["&", (field_name, '>=', start), (field_name, '<', end)]

    if val == "this_year":
        start = current_date.replace(month=1, day=1)
        end = start + relativedelta(years=1)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    if val == "last_day":
        start = current_date - timedelta(days=1)
        return ["&", (field_name, ">=", start), (field_name, "<", current_date)]

    if val == "last_week":
        end = current_date - timedelta(days=current_date.weekday())
        start = end - timedelta(days=7)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    if val == "last_month":
        start = (current_date - relativedelta(months=1)).replace(day=1)
        end = start + relativedelta(months=1)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    if val == "last_quarter":
        start_of_this_quarter = datetime(current_date.year, ((current_date.month - 1) // 3) * 3 + 1, 1)
        end = start_of_this_quarter
        start = end - relativedelta(months=3)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    if val == "last_year":
        # ⚠️ CORREGIDO: El original tenía start y end invertidos
        start = datetime(current_date.year - 1, 1, 1)
        end = datetime(current_date.year, 1, 1)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    if val == "last_7_days":
        start = current_date - timedelta(days=7)
        return [(field_name, ">=", start)]

    if val == "last_30_days":
        start = current_date - timedelta(days=30)
        return [(field_name, ">=", start)]

    if val == "last_90_days":
        start = current_date - timedelta(days=90)
        return [(field_name, ">=", start)]

    if val == "last_365_days":
        start = current_date - timedelta(days=365)
        return [(field_name, ">=", start)]

    if val == "next_day":
        start = current_date + timedelta(days=1)
        end = start + timedelta(days=1)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    if val == "next_week":
        start = current_date + timedelta(days=(7 - current_date.weekday()))
        end = start + timedelta(days=7)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    if val == "next_month":
        start = (current_date + relativedelta(months=1)).replace(day=1)
        end = (start + relativedelta(months=1)).replace(day=1)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    if val == "next_quarter":
        end_of_this_quarter = datetime(current_date.year, (((current_date.month - 1) // 3) * 3 + 3) + 1, 1)
        start = end_of_this_quarter
        end = (start + relativedelta(months=3)).replace(day=1)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    if val == "next_year":
        start = datetime(current_date.year + 1, 1, 1)
        end = datetime(current_date.year + 2, 1, 1)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    # ⚠️ CORREGIDO: Si el valor no coincide, retornar lista vacía en lugar de [tuple(domain)]
    return []
