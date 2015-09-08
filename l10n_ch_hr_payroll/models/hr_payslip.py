# -*- coding: utf-8 -*-
#
#  File: models/hr_payslip.py
#  Module: l10n_ch_hr_payroll
#
#  Created by cyp@open-net.ch
#
#  Copyright (c) 2015-TODAY Open-Net Ltd.
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


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # ---------- Fields management

    reimbursements = fields.One2many('account.invoice', 'slip_id',
        string='Reimbursements')
    commissions = fields.One2many('hr.expense.expense', 'slip_id',
        string='Commissions')

    # ---------- Utilities
    
    @api.multi
    def compute_sheet(self):

        slip_ids = [x.id for x in self]

        # First, detach invoices from the pay slips
        InvoiceObj = self.env['account.invoice']
        invoices = InvoiceObj.search([('slip_id', 'in', slip_ids)])
        if invoices:
            invoices.write({'slip_id':False})
    
        # Second, detach expenses from the pay slips
        ExpenseObj = self.env['hr.expense.expense']
        expenses = ExpenseObj.search([('slip_id', 'in', slip_ids)])
        if expenses:
            expenses.write({'slip_id':False})

        # Then, re-link the invoices and the expenses using the criterias
        InvoiceLineObj = self.env['account.invoice.line']
        for payslip in self:
            # No contract? forget about it
            if not payslip.contract_id:
                continue
            
            # No user? forget about it
            user_id = payslip.contract_id.employee_id.user_id and \
                payslip.contract_id.employee_id.user_id.id or False
            if not user_id:
                continue
            employee_id = payslip.contract_id.employee_id.id

            # Look for invoice lines
            inv_ids = []
            filters = [
                ('invoice_id.user_id', '=', user_id),
                ('invoice_id.slip_id', '=', False),
                ('product_id', '!=', False),
                ('invoice_id.state', '=', 'paid'),
                ('invoice_id.type', '=', 'out_invoice'),
            ]
            for invl in InvoiceLineObj.search(filters):
                if invl.invoice_id.id not in inv_ids:
                    inv_ids.append(invl.invoice_id.id)
                    invl.invoice_id.write({'slip_id': payslip.id})

            # Look for expenses
            exp_ids = []
            filters = [
                ('employee_id', '=', employee_id),
                ('slip_id', '=', False),
                ('state', '=', ['done','accepted']),
            ]
            expenses = ExpenseObj.search(filters)
            if expenses:
                expenses.write({'slip_id': payslip.id})

        return super(HrPayslip, self).compute_sheet()
