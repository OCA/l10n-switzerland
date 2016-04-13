# -*- coding: utf-8 -*-
#
#  File: __openerp__.py
#  Module: l10n_ch_payroll_attendances
#
#  Created by dco@open-net.ch
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
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Attendances - Timesheet',
    'summary': 'Attendances and timesheet improvements',
    'category': 'Human Resources',
    'author': "Open-Net Sàrl",
    'depends': [
        'hr_payroll'
    ],
    'version': '9.0.1.0.0',
    'auto_install': False,
    'website': 'http://open-net.ch',
    'license': 'AGPL-3',
    'images': [],
    'data': [
        'views/res_calendar_view.xml',
        'views/hr_payroll_view.xml',
        'views/hr_contract_view.xml',
        'data/salary_rules.xml',
    ],
    'installable': True
}
