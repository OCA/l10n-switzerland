# -*- coding: utf-8 -*-
# Copyright 2017 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo.addons.decimal_precision as dp
from odoo import fields, models


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
        default=12350,
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

    # AS Families (PC Famille)
    pc_f_vd_per = fields.Float(
        string="Percentage (%)",
        default='-0.06',
        digits=dp.get_precision('Payroll Rate'),
        required=False)

    # OBP(LPP)
    lpp_min = fields.Float(
        string="Minimum legal",
        default=1762.50,
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

    # -Family Allowances-
    fa_amount_child = fields.Float(
        string="Amount per child (0-16)",
        default='0',
        digits=dp.get_precision('Account'),
        required=False)
    fa_amount_student = fields.Float(
        string="Amount per student (16+)",
        default='0',
        digits=dp.get_precision('Account'),
        required=False)
    fa_min_number_childs = fields.Integer(
        string="Additional allowance for the",
        default='3',
        required=False)
    fa_amount_additional = fields.Float(
        string="Additional allowance amount",
        default='0',
        digits=dp.get_precision('Account'),
        required=False)
