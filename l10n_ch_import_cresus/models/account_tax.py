# -*- coding: utf-8 -*-
# Copyright 2015 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class AccountTax(models.Model):
    _inherit = "account.tax"

    tax_cresus_mapping = fields.Char(
        string='Cresus tax name')
