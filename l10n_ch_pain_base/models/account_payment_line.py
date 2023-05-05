# copyright 2016 Akretion - Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountPaymentLine(models.Model):
    _inherit = "account.payment.line"

    local_instrument = fields.Selection(
        selection_add=[("CH01", "CH01 (ISR)")], ondelete={"CH01": "set null"}
    )
    communication_type = fields.Selection(
        selection_add=[("isr", "ISR"), ("qrr", "QRR")],
        ondelete={"isr": "set default", "qrr": "set default"},
    )

    def invoice_reference_type2communication_type(self):
        res = super().invoice_reference_type2communication_type()
        res["isr"] = "isr"
        return res
