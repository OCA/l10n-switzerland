# -*- coding: utf-8 -*-
# © 2016 Coninckx David (Open Net Sarl)
# © 2017 Leonardo Franja (Open Net Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Expense - Payroll',
    'summary': 'Payroll Expense',
    'category': 'Human Resources',
    'author': "Open Net Sàrl",
    'depends': [
        'hr_payroll',
        'hr_expense'
    ],
    'version': '10.0.1.0.0',
    'auto_install': False,
    'website': 'http://open-net.ch',
    'license': 'AGPL-3',
    'images': [],
    'data': [
        'views/hr_payroll_view.xml',
        'data/hr.salary.rule.category.xml',
        'data/hr.salary.rule.xml'
    ],
    'installable': True
}
