# -*- coding: utf-8 -*-
#
#  File: models/hr_contract.py
#  Module: l10n_ch_hr_payroll
#
#  Created by cyp@open-net.ch
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


from openerp import models, fields, api
import openerp.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class HrContract(models.Model):
    _inherit = 'hr.contract'

    # ---------- Fields management

    def _comp_wage_expenses(self):
        self.reimbursement = 0
        self.commission = 0

        # Look in linked invoice lines
        if self.employee_id.user_id:
            filters = [
                ('invoice_id.user_id', '=', self.employee_id.user_id.id),
                ('invoice_id.slip_id', '=', self.id),
                ('product_id', '!=', False),
                ('invoice_id.state', '=', 'paid'),
                ('invoice_id.type', '=', 'out_invoice'),
            ]
            InvoiceLineObj = self.env['account.invoice.line']
            for invl in InvoiceLineObj.search(filters):
                if invl.product_id.hr_expense_ok:
                    self.reimbursement += invl.price_subtotal
                    continue
                self.commission += invl.price_subtotal

        # Look in linked expenses
        filters = [
            ('employee_id', '=', self.employee_id.id),
            ('slip_id', '=', self.id),
            ('state', 'in', ['done','accepted']),
        ]
        ExpensesObj = self.env['hr.expense.expense']
        for expense in ExpensesObj.search(filters):
            self.commission += expense.amount


    lpp_rate = fields.Float(string='LPP Rate',
        digits=dp.get_precision('Payroll Rate'))
    lpp_amount = fields.Float(string='LPP Amount',
        digits=dp.get_precision('Account'))
    worked_hours = fields.Float(string='Worked Hours')
    hourly_rate = fields.Float(string='Hourly Rate')
    holiday_rate = fields.Float(string='Holiday Rate')
    reimbursement = fields.Float(string='Reimbursement',
        compute='_comp_wage_expenses')
    commission = fields.Float(string='Commission',
        compute='_comp_wage_expenses')
    comm_rate = fields.Float(string='Commissions Rate',
        digits=dp.get_precision('Payroll Rate'))

    # ---------- Utilities

    @api.multi
    def compute_wage(self, worked_hours, hourly_rate):
        """
            Compute the wage from worked_hours and hourly_rate.
        """
        wage = worked_hours * hourly_rate

        res = {
            'value': { 'wage': wage }
        }
        return res
