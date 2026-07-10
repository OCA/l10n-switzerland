# Copyright 2015 Camptocamp SA
# Copyright 2016 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    tax_cresus_mapping = fields.Char(string="Crésus tax name")
