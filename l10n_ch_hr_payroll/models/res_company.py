# -*- coding: utf-8 -*-
# © 2017 Leonardo Franja (Opennet Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import openerp.addons.decimal_precision as dp
from odoo import fields, models, api


class LPPContract(models.Model):
    _name = 'lpp.contract'

    company_id = fields.Many2one(
        string='Company',
        invisible=True,
        comodel_name='res.company')

    contract_id = fields.One2many(
        string="Contract id's",
        comodel_name='hr.contract',
        inverse_name='lpp_contract_id',
        required=True)

    name = fields.Char(
        string='Contract name',
        required=True)

    dc_amount = fields.Float(
        string='Deduction Amount',
        required=True)


class ResCompany(models.Model):
    _inherit = 'res.company'

    # -Parameters-
    # UI(AC)
    ac_limit = fields.Float(
        string='Maximum limit',
        default='10500',
        digits=dp.get_precision('Account'),
        required=False)
    ac_per_off_limit = fields.Float(
        string='Percentage (off limit) (%)',
        default='-1.0',
        digits=dp.get_precision('Payroll Rate'),
        required=False)
    ac_per_in_limit = fields.Float(
        string='Percentage (%)',
        default='-1.1',
        digits=dp.get_precision('Payroll Rate'),
        required=False)

    # OAI(AVS)
    avs_per = fields.Float(
        string='Percentage (%)',
        default='-5.125',
        digits=dp.get_precision('Payroll Rate'),
        required=False)

    # FADMIN
    fadmin_per = fields.Float(
        string="Percentage (%)",
        digits=dp.get_precision('Payroll Rate'),
        required=False)

    # AI(LAA)
    laa_per = fields.Float(
        string="Percentage (%)",
        digits=dp.get_precision('Payroll Rate'),
        required=False)

    # SDA(LCA)
    lca_per = fields.Float(
        string="Percentage (%)",
        digits=dp.get_precision('Payroll Rate'),
        required=False)

    # OBP(LPP)
    lpp_min = fields.Float(
        string="Minimum legal",
        default='2056.25',
        digits=dp.get_precision('Account'),
        required=False)
    lpp_max = fields.Float(
        string="Maximum legal",
        default='7050.00',
        digits=dp.get_precision('Account'),
        required=False)
    lpp_contract_ids = fields.One2many(
        string="OBP contract ids",
        comodel_name='lpp.contract',
        inverse_name='company_id')

    @api.multi
    def write(self, values):
        for company in self:
            res = super(ResCompany, company).write(values)

            ids_to_unlink = self.env['lpp.contract'].search([
                ('company_id', '=', False)
            ])
            ids_to_unlink.unlink()
            return res
