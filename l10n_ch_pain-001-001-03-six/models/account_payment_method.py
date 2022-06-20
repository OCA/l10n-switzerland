# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    pain_version = fields.Selection(
        selection_add=[
            ("pain.001.001.03.ch.02",
            "pain.001.001.03.ch.02 (credit transfer swiss practice (SPS))"),
        ],
        ondelete={
            "pain.001.001.03.ch.02": "set null",
        },
    )

    def get_xsd_file_path(self):
        self.ensure_one()
        if self.pain_version = "pain.001.001.03.ch.02"
            path = (
                "l10n_ch_pain-001-001-03-six/data/pain-001-001-03-six.xsd"
            )
            return path
        return super().get_xsd_file_path()

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res["sepa_credit_transfer_chf"] = {
            "mode": "multi",
            "domain": [("type", "=", "bank")],
        }
        return res
