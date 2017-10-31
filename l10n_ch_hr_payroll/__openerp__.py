# -*- coding: utf-8 -*-
#
#  File: __openerp__.py
#  Module: l10n_ch_hr_payroll
#
#  Created by sge@open-net.ch
#
#  Copyright (c) 2014-TODAY Open-Net Ltd. <http://www.open-net.ch>
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP S.A. <http://www.openerp.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
##############################################################################
#
#    License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Switzerland - Payroll',
    'summary': 'Switzerland Payroll Rules',
    'category': 'Localization',
    'author': "Open Net Sàrl,Odoo Community Association (OCA)",
    'depends': [
        'decimal_precision',
        'hr_payroll',
        'hr_payroll_account',
        'hr_contract',
        'hr_attendance',
        'account'
    ],
    'version': '9.0.1.4.0',
    'auto_install': False,
    'demo': [],
    'website': 'http://open-net.ch',
    'license': 'AGPL-3',
    'data': [
        'data/hr.salary.rule.category.xml',
        'data/hr.salary.rule.xml',
        'views/hr_employee_view.xml',
        'views/hr_contract_view.xml'
    ],
    'installable': True
}
