# -*- coding: utf-8 -*-
#################################################################################
# Author      : Terabits Technolab (<www.terabits.xyz>)
# Copyright(c): 2023-2025
# All Rights Reserved.
#################################################################################
{
    "name": "Advanced Web Domain Widget",
    "version": "19.0.3.3.0",
    "summary": "Set all relational fields domain by selecting its records using `in, not in` operator.",
    "sequence": 10,
    "author": "Terabits Technolab",
    "license": "OPL-1",
    "website": "https://www.terabits.xyz",
    "description": """
        Advanced Web Domain Widget for Odoo 19.
    """,
    "price": "29.00",
    "currency": "USD",
    "depends": ["web"],
    "data": [
        # 'views/assets.xml',
    ],
    "assets": {
        # ⚠️ Odoo 19: web._assets_core fue eliminado, usar solo web.assets_backend
        "web.assets_backend": [
            "advanced_web_domain_widget/static/src/domain/domain_field.js",
            "advanced_web_domain_widget/static/src/tree_editor/tree_editor_autocomplete.js",
            "advanced_web_domain_widget/static/src/tree_editor/tree_editor_operator_editor.js",
            "advanced_web_domain_widget/static/src/tree_editor/tree_editor_value_editors.js",
            "advanced_web_domain_widget/static/src/tree_editor/tree_editor.js",
            "advanced_web_domain_widget/static/src/domain_selector/domain_selector_operator_editor.js",
            "advanced_web_domain_widget/static/src/domain_selector/domain_selector.js",
            "advanced_web_domain_widget/static/src/domain_selector_dialog/domain_selector_dialog.js",
            "advanced_web_domain_widget/static/src/dateSelectionBits/dateSelectionBits.js",
            "advanced_web_domain_widget/static/src/model_field_selector/model_field_selector.js",
            # Templates XML de OWL
            "advanced_web_domain_widget/static/src/domain/domain_field.xml",
            "advanced_web_domain_widget/static/src/tree_editor/tree_editor.xml",
            "advanced_web_domain_widget/static/src/domain_selector/domain_selector.xml",
            "advanced_web_domain_widget/static/src/domain_selector_dialog/domain_selector_dialog.xml",
            "advanced_web_domain_widget/static/src/dateSelectionBits/dateSelectionBits.xml",
            "advanced_web_domain_widget/static/src/model_field_selector/model_field_selector.xml",
        ],
    },
    "images": ["static/description/banner.png"],
    "application": True,
    "installable": True,
    "auto_install": False,
}
