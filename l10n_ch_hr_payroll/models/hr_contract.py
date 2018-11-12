# -*- coding: utf-8 -*-
# Copyright 2017 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api
import odoo.addons.decimal_precision as dp


class HrContract(models.Model):
    _inherit = 'hr.contract'

    lpp_rate = fields.Float(
        string='Taux LPP (%)')
    lpp_amount = fields.Float(
        string='Montant LPP')

    imp_src_barem = fields.Char(string="Barème imp. source")
    is_eccle = fields.Boolean(string="Soumis à l'impôt ecclésiastique")
