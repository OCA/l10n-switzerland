# -*- coding: utf-8 -*-
# Copyright 2017 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Switzerland - Payroll',
    'summary': 'Switzerland Payroll Rules',
    'category': 'Localization',
    'author': "Open Net Sàrl,Odoo Community Association (OCA)",
    'depends': [
        'hr_payroll_account',
        'hr_contract',
        'hr_attendance'
    ],
    'version': '10.0.1.0.0',
    'auto_install': False,
    'demo': [],
    'website': 'http://open-net.ch',
    'license': 'AGPL-3',
    'data': [
        'data/hr_salary_rule_category.xml',
        'views/hr_employee_view.xml',
        'views/hr_contract_view.xml',
        'views/hr_imp_src_view.xml',
        'views/hr_payslip_view.xml',
    ],
    'installable': True
}
