# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    force_swiss_qr_invoice = fields.Boolean(
        "Force sending swiss QR invoice",
        help="Check this box to force sending swiss QR invoice to international"
        " customers",
    )
