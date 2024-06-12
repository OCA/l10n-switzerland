# copyright 2016 Akretion - Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountPaymentLine(models.Model):
    _inherit = "account.payment.line"

    communication_type = fields.Selection(
        selection_add=[("qrr", "QRR")],
        ondelete={ "qrr": "set default"},
    )
