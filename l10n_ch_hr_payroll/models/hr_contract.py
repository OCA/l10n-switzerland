# -*- coding: utf-8 -*-
#
#  File: models/hr_contract.py
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


from openerp import models, fields, api
import openerp.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class HrContract(models.Model):
    _inherit = 'hr.contract'

    # ---------- Fields management

    @api.one
    @api.depends('employee_id.user_id')
    def _comp_wage_expenses(self):
        self.reimbursement = 0
        self.commission = 0

        # Look in linked expenses:
        filters = [
            ('employee_id', '=', self.employee_id.id),
            ('slip_id', '=', False),
            ('state', 'in', ['done', 'accepted']),
        ]
        ExpensesObj = self.env['hr.expense.expense']
        for expense in ExpensesObj.search(filters):
            self.reimbursement += expense.amount

        # Now: find the paid invoice lines
        # But we'll use the corresponding account move line
        # used to reconcile them, and linked to liquidity-type accounts
        moves = {}
        query = """select inv.id,invl.id,t.hr_expense_ok,invl.price_subtotal, inv.move_id
from account_invoice inv, account_invoice_line invl,
product_product p, product_template t
where inv.user_id=%d
and inv.state in ('open','paid')
and inv.type='out_invoice'
and inv.id=invl.invoice_id
and invl.product_id=p.id
and p.product_tmpl_id=t.id
order by inv.id,invl.id""" % self.employee_id.user_id.id
        self._cr.execute(query)
        for row in self._cr.fetchall():
            if row[4] not in moves:
                moves[row[4]] = {'exp_yes': 0, 'exp_no': 0, 'tot': 0}
            col = 'exp_yes' if row[2] else 'exp_no'
            moves[row[4]][col] += row[3]
            moves[row[4]]['tot'] += row[3]

        # Compute % in favor of what is expenses
        # and look for the corresponding move lines used for the reconcilations
        # and linked to liquidity accounts
        for move_id in moves.keys():
            if moves[move_id]['tot'] != 0:
                factor = moves[move_id]['exp_yes'] / moves[move_id]['tot']
            else:
                factor = 0
            if move_id:
                query = """select sum(l3.debit)
                    from account_move_line l1, account_move_line l2,
                    account_move_line l3,
                    account_account a
                    where l1.move_id=%d
                    and (
                    (l1.reconcile_id=l2.reconcile_id and l2.reconcile_id != 0)
                      or
                    (l1.reconcile_partial_id=l2.reconcile_partial_id
                     and l2.reconcile_partial_id != 0))
                    and l3.move_id=l2.move_id
                    and (l3.reconcile_id=0 or l3.reconcile_id is null)
                    and (l3.reconcile_partial_id=0
                         or l3.reconcile_partial_id is null)
                    and l3.account_id=a.id
                    and (l3.slip_id=0 or l3.slip_id is null)
                    and a.type='liquidity'""" % move_id
                self._cr.execute(query)
                row = self._cr.fetchone()
                self.reimbursement += (row[0] or 0) * factor
                self.commission += (row[0] or 0) * (1.0 - factor)

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
            'value': {'wage': wage}
        }
        return res
