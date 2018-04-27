# -*- coding: utf-8 -*-
# © 2016 Coninckx David (Open Net Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    expense_ids = fields.One2many(
        'hr.expense.sheet', 'slip_id', string='Expenses')

    @api.multi
    def compute_sheet(self):
        for payslip in self:

            # Detach expenses from the pay slips
            expense_sheet = payslip.env['hr.expense.sheet']
            employee_id = payslip.employee_id.id

            # Look for expenses
            filters = [
                ('employee_id', '=', employee_id),
                ('slip_id', '=', False),
                ('state', '=', 'approve'),
            ]
            expenses = expense_sheet.search(filters)
            if expenses:
                expenses.write({'slip_id': payslip.id})

            res = super(HrPayslip, payslip).compute_sheet()
        return res

    def action_payslip_done(self):
        hr_expense = self.env['hr.expense']
        expense_sheet = self.env['hr.expense.sheet']
        expenses = expense_sheet.search([
            ('slip_id', '=', self.id)
        ])
        for expense in expenses:
            expense.state = 'done'
            hr_expense_s = hr_expense.search([
                ('sheet_id', '=', expense.id)
            ])

            hr_expense_s.write({
                'state': 'done'
            })
        return super(HrPayslip, self).action_payslip_done()
