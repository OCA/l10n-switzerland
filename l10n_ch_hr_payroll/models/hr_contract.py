# Copyright 2017 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api
import odoo.addons.decimal_precision as dp


class HrContract(models.Model):
    _inherit = 'hr.contract'

    lpp_rate = fields.Float(
        string='OBP Rate (%)',
        digits=dp.get_precision('Payroll Rate'))
    lpp_amount = fields.Float(
        string='OBP Amount',
        digits=dp.get_precision('Account'))
    lpp_contract_id = fields.Many2one(
        string='OBP Contract',
        comodel_name='lpp.contract',
        inverse_name='contract_id')

    imp_src = fields.Float(
        string='Source Tax (%)',
        digits=dp.get_precision('Payroll Rate'))

    wage_type = fields.Selection(
        string="Wage Type",
        selection=[('month', "Monthly"), ('hour', "Hourly")],
        default='month')
    wage_fulltime = fields.Float(
        string='Full-time Wage',
        digits=dp.get_precision('Account'),
        default=0)
    occupation_rate = fields.Float(
        string='Occupation Rate (%)',
        digits=dp.get_precision('Account'),
        default=100.0)

    provision_13_salary = fields.Float(
        string='Accumulated 13th salary (Bruto)',
        compute='_compute_13_salary',
        digits=dp.get_precision('Account'))

    @api.onchange('occupation_rate', 'wage_fulltime')
    def _onchange_wage_rate_fulltime(self):
        for contract in self:
            contract.wage = \
                contract.wage_fulltime * (contract.occupation_rate / 100)

    def _compute_13_salary(self):
        account_id = self.env.ref(
            'l10n_ch_hr_payroll.PROVISION_13').account_credit.id
        for contract in self:
            move_lines = self.env['account.move.line'].search([
                ('partner_id', '=', contract.employee_id.address_home_id.id),
                ('account_id', '=', account_id),
            ])
            contract.provision_13_salary = sum(move_lines.mapped('credit')) - \
                sum(move_lines.mapped('debit'))
