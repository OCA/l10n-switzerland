# -*- coding: utf-8 -*-
# Copyright 2016 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class account_tax(models.Model):
    _inherit = "account.tax"

    tax_winbiz_mapping = fields.Char(
        size=128,
        string='WinBIZ tax code')
