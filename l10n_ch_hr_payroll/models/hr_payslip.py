# -*- coding: utf-8 -*-
# © 2017 Leonardo Franja (Opennet Sarl)
# License into __openerp__.py.

from odoo import fields, models, api


class HrPayslip(models.Model):

    _inherit = 'hr.payslip'

    working_days = fields.Integer(
        string='Number of working days')
    non_working_days = fields.Integer(
        string='Number of non-working days (not payable)')
    working_rate = fields.Float(
        string='Working Rate (%)',
        readonly=True)

    @api.onchange('working_days', 'non_working_days')
    def _onchange_worked_non_working_days(self):
        for payslip in self:
            if payslip.working_days != 0:
                worked_days = payslip.working_days - payslip.non_working_days
                payslip.working_rate = \
                    worked_days/float(payslip.working_days)*100

    @api.multi
    def compute_sheet(self):
        for payslip in self:
            payslip._onchange_worked_non_working_days()
            res = super(HrPayslip, payslip).compute_sheet()
        return res


class HrPayslipLine(models.Model):

    _inherit = 'hr.payslip.line'

    python_rate = fields.Float(
        compute='_compute_python_rate',
        string='Rate (%)',
        store=True)
    python_amount = fields.Float(
        compute='_compute_python_amount',
        string='Amount',
        store=True)

    @api.depends('quantity', 'amount', 'rate')
    def _compute_python_rate(self):
        for line in self:
            if line.salary_rule_id.percentage:
                line.python_rate = line.salary_rule_id.percentage
            elif line.rate:
                line.python_rate = line.rate
            else:
                line.python_rate = 100

    @api.depends('quantity', 'amount', 'rate')
    def _compute_python_amount(self):
        for line in self:
            if line.salary_rule_id.amount_base:
                line.python_amount = line.salary_rule_id.amount_base
            elif line.amount:
                line.python_amount = line.amount
            else:
                line.python_amount = 0
