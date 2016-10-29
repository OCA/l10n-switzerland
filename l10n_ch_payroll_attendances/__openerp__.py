# -*- coding: utf-8 -*-
# © 2016 Open Net Sarl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Attendances - Timesheet',
    'summary': 'Attendances and timesheet improvements',
    'category': 'Human Resources',
    'author': "Open-Net Sàrl, Odoo Community Association (OCA)",
    'depends': [
        'hr_payroll'
    ],
    'version': '9.0.1.0.2',
    'auto_install': False,
    'website': 'http://open-net.ch',
    'license': 'AGPL-3',
    'images': [],
    'data': [
        'views/res_calendar_view.xml',
        'views/hr_payroll_view.xml',
        'views/hr_contract_view.xml',
        'data/salary_rules.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True
}
