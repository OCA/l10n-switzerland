# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import io

from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf(self, res_ids=None, data=None):
        reports = ["account_credit_control.report_credit_control_summary"]
        if (
            self.report_name in reports
            and self.env.user.company_id.credit_ctrl_print_invoice
        ):
            io_list = []
            for cred_ctr in self.env["credit.control.communication"].browse(res_ids):
                cred_ctr_pdf, _ = super()._render_qweb_pdf(cred_ctr.id, data)
                io_list.append(io.BytesIO(cred_ctr_pdf))
                invoices = cred_ctr.mapped("credit_control_line_ids.invoice_id")
                inv_report = self._get_report_from_name(
                    "l10n_ch_invoice_reports.account_move_payment_report"
                )
                for inv in invoices:
                    invoice_pdf, _ = inv_report._render_qweb_pdf(inv.id, data)
                    io_list.append(io.BytesIO(invoice_pdf))
            pdf = self.merge_pdf_in_memory(io_list)
            for io_file in io_list:
                io_file.close()
            return (pdf, "pdf")
        else:
            return super()._render_qweb_pdf(res_ids, data)
