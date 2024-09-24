# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import io
from collections import OrderedDict

from odoo import api, models


class ReportSwissQR(models.AbstractModel):
    _inherit = "report.l10n_ch.qr_report_main"

    @api.model
    def _get_report_values(self, docids, data=None):
        """Replace QR URL to consider dunning fees"""
        self = self.with_context(credit_control_run_print_report=True)
        res = super()._get_report_values(docids, data=data)
        dunning_fees_qr_amounts = self.env.context.get("qr_dunning_fees_amounts", {})
        if not dunning_fees_qr_amounts:
            return res
        qr_code_urls = {}
        invoices = self.env["account.move"].browse(docids)
        for invoice in invoices:
            if invoice.id not in dunning_fees_qr_amounts:
                continue
            qr_code_urls[invoice.id] = invoice.partner_bank_id.build_qr_code_base64(
                dunning_fees_qr_amounts[invoice.id],
                invoice.ref or invoice.name,
                invoice.payment_reference,
                invoice.currency_id,
                invoice.partner_id,
                qr_method="ch_qr",
                silent_errors=False,
            )
        res["qr_code_urls"].update(qr_code_urls)
        return res
