# -*- coding: utf-8 -*-

{
    'name' : 'Sale Order Discount Approval App',
    'author': "Edge Technologies",
    'version' : '17.0.1.0',
    'live_test_url':'https://youtu.be/zDiuk7LB5LI',
    "images":['static/description/main_screenshot.png'],
    'summary' : 'Sale discount approval workflow on sale order discount approval sales discount approval for sales order discount approval sale discount validation sale order discount validation sale discount double validation discount approval on sales order discount',
    'description' : """ This module allows restricting discounts on the sale order lines. 
                        if the user gives more discount than allowed then the sales order 
                        goes for approval with discount approval manager. approval manager 
                        gets approval email with order link and they can approve the order.""",
    "license" : "OPL-1",
    'depends' : ['base','sale_management','account'],
    'data' : [
        'security/groups.xml',
        'data/mail_template.xml',
        'views/res_users_view.xml',
        'views/sale_order_view.xml',
    ],
    'installable' : True,
    'auto_install' : False,
    'price': 9,
    'currency': "EUR",
    'category' : 'Sales',
}
