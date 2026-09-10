# -*- coding: utf-8 -*-
#################################################################################
# Domain preparation utilities
# Migrado desde advanced_web_domain_widget para Odoo 19
#################################################################################

from odoo.http import request
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def compute_domain(domain_tuple, model, env=None):
    """
    Reemplaza 0 con el ID del usuario/empresa actual en campos many2one/many2many
    que apuntan a res.users o res.company.
    
    IMPORTANTE: Retorna un NUEVO domain_tuple (no modifica in-place, porque las
    tuplas son inmutables).
    
    :param domain_tuple: Una tupla del dominio
    :param model: Nombre del modelo
    :param env: Environment de Odoo (opcional, usa request.env si no se pasa)
    :return: domain_tuple modificado
    """
    if not isinstance(domain_tuple, (tuple, list)) or len(domain_tuple) != 3:
        return domain_tuple

    left_value = domain_tuple[0]
    operator_value = domain_tuple[1]
    right_value = domain_tuple[2]
    
    # Hacer copia para no modificar el original
    if isinstance(right_value, list):
        right_value = list(right_value)
    
    left_value_split_list = left_value.split('.')
    left_user = False
    left_company = False
    
    # Odoo 19: usar env pasado o request.env
    if env is None:
        env = request.env if request else None
    if not env:
        return (left_value, operator_value, right_value)
    
    field_obj = env['ir.model.fields']
    
    for field_name in left_value_split_list:
        left_user = False
        left_company = False
        model_obj = env[model]
        field = field_obj.search([
            ('model_id.model', '=', model_obj._name),
            ('name', '=', field_name)
        ], limit=1)
        
        if field and field.ttype in ['many2one', 'many2many', 'one2many']:
            field_relation = field.relation
            if field_relation == 'res.users':
                left_user = True
            if field_relation == 'res.company':
                left_company = True
    
    if left_user and operator_value in ['in', 'not in']:
        if isinstance(right_value, list) and 0 in right_value:
            zero_index = right_value.index(0)
            right_value[zero_index] = env.user.id

    if left_company and operator_value in ['in', 'not in']:
        if isinstance(right_value, list) and 0 in right_value:
            zero_index = right_value.index(0)
            right_value[zero_index] = env.company.id
    
    return (left_value, operator_value, right_value)


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

    current_date = datetime.now()
    current_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0)

    if operator != "date_filter":
        return [tuple(domain)]

    # ---- Today ----
    if val == "today":
        start = current_date
        end = current_date + timedelta(days=1)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    # ---- This Week ----
    if val == "this_week":
        start = current_date - timedelta(days=current_date.weekday())
        end = start + timedelta(days=7)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    # ---- This Month ----
    if val == "this_month":
        start = current_date.replace(day=1)
        end = start + relativedelta(months=1)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    # ---- This Quarter ----
    if val == "this_quarter":
        start = datetime(current_date.year, ((current_date.month - 1) // 3) * 3 + 1, 1)
        end = start + relativedelta(months=3)
        return ["&", (field_name, '>=', start), (field_name, '<', end)]

    # ---- This Year ----
    if val == "this_year":
        start = current_date.replace(month=1, day=1)
        end = start + relativedelta(years=1)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    # ---- Last Day ----
    if val == "last_day":
        start = current_date - timedelta(days=1)
        return ["&", (field_name, ">=", start), (field_name, "<", current_date)]

    # ---- Last Week ----
    if val == "last_week":
        end = current_date - timedelta(days=current_date.weekday())
        start = end - timedelta(days=7)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    # ---- Last Month ----
    if val == "last_month":
        start = (current_date - relativedelta(months=1)).replace(day=1)
        end = start + relativedelta(months=1)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    # ---- Last Quarter ----
    if val == "last_quarter":
        start_of_this_quarter = datetime(current_date.year, ((current_date.month - 1) // 3) * 3 + 1, 1)
        end = start_of_this_quarter
        start = end - relativedelta(months=3)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    # ---- Last Year ----
    if val == "last_year":
        start = datetime(current_date.year - 1, 1, 1)
        end = datetime(current_date.year, 1, 1)
        return ["&", (field_name, ">=", start), (field_name, "<", end)]

    # ---- Last N Days ----
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

    # ---- Next Day/Week/Month/Quarter/Year ----
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

    # Si el valor no coincide, retornar lista vacía
    return []
