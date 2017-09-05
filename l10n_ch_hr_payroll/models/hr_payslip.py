# -*- coding: utf-8 -*-
# Copyright 2017 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo.addons.decimal_precision as dp
from datetime import timedelta
from odoo import fields, models, api


class HrPayslip(models.Model):

    _inherit = 'hr.payslip'

    working_days = fields.Integer(
        string='Number of working days')
    non_working_days = fields.Integer(
        string='Number of non-working days (not payable)')
    working_rate = fields.Float(
        string='Working Rate (%)',
        readonly=True,
        default=100)
    worked_hours = fields.Float(
        string='Number of worked hours',
        readonly=True,
        compute='_compute_worked_hours')

    wage_type = fields.Selection(related='contract_id.wage_type')

    @api.multi
    def _compute_worked_hours(self):
        for payslip in self:
            if payslip.contract_id.wage_type == 'hour':
                dt = fields.Datetime
                date_to = dt.from_string(payslip.date_to)
                date_to = dt.to_string(date_to + timedelta(days=1))

                all_time_records = self.env['hr.attendance'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('check_in', '>=', payslip.date_from),
                    ('check_in', '<', date_to)
                ])
                sum_all_hours = 0
                for time_rec in all_time_records:
                    sum_all_hours += time_rec.worked_hours

                sum_minutes = (sum_all_hours - int(sum_all_hours))*60
                sum_secunds = (sum_minutes - int(sum_minutes))/60
                sum_wo_sec = sum_all_hours - sum_secunds

                payslip.worked_hours = sum_wo_sec

    @api.onchange('employee_id', 'date_from', 'date_to')
    def _onchange_employee_worked_hours(self):
        for payslip in self:
            payslip._compute_worked_hours()

    @api.onchange('working_days', 'non_working_days')
    def _onchange_working_non_working_days(self):
        for payslip in self:
            if payslip.working_days != 0:
                worked_days = payslip.working_days - payslip.non_working_days
                payslip.working_rate = \
                    worked_days/float(payslip.working_days)*100
            elif payslip.working_days == 0 and payslip.non_working_days == 0:
                payslip.working_rate = 100

    @api.multi
    def compute_sheet(self):
        for payslip in self:
            payslip._onchange_working_non_working_days()
            payslip._onchange_employee_worked_hours()
            res = super(HrPayslip, payslip).compute_sheet()
        return res


class HrPayslipLine(models.Model):

    _inherit = 'hr.payslip.line'

    python_rate = fields.Float(
        compute='_compute_python_rate',
        string='Rate (%)',
        digits=dp.get_precision('Payroll Rate'),
        store=True)
    python_amount = fields.Float(
        compute='_compute_python_amount',
        string='Amount',
        digits=dp.get_precision('Account'),
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
