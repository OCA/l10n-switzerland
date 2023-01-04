# Copyright 2014 Olivier Jossen brain-tec AG
# Copyright 2014 Guewen Baconnier (Camptocamp SA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResBank(models.Model):
    _inherit = "res.bank"

    branch_code = fields.Char()
