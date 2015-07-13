# -*- coding: utf-8 -*-
#
#  File: hr_contract.py
#  Module: l10n_ch_hr_payroll
#
#  Created by sge@open-net.ch
#
#  Copyright (c) 2015 Open-Net Ltd.
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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


from openerp.osv import fields, orm
import openerp.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class hr_contract(orm.Model):
    _inherit = 'hr.contract'
    _columns = {
        'lpp_rate': fields.float('LPP Rate',
                                 digits_compute=dp.get_precision(
                                     'Payroll Rate')),
        'lpp_amount': fields.float('LPP Amount',
                                   digits_compute=dp.get_precision(
                                       'Account')),
        'worked_hours': fields.float('Worked Hours'),
        'hourly_rate': fields.float('Hourly Rate'),
        'holiday_rate': fields.float('Holiday Rate')
        }

    def compute_wage(self, cr, uid, id,
                     worked_hours, hourly_rate,
                     context=None):
        """
        Compute the wage from worked_hours and hourly_rate.
        wage = worked_hours * hourly_rate
        """
        res = {'value': {}}
        wage = worked_hours * hourly_rate
        res['value'] = {
            'wage': wage,
        }
        return res
