# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import models


class Report(models.Model):
    """Print pay slip form credit line"""

    _inherit = "ir.actions.report"

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        credit_control_communication_report_name = (
            "account_credit_control.report_credit_control_summary"
        )
        report = self._get_report(report_ref)
        report_name = report.report_name
        if report_name != credit_control_communication_report_name:
            return super()._render_qweb_pdf_prepare_streams(
                report_ref, data, res_ids=res_ids
            )

        collected_streams = OrderedDict()
        communications = self.env["credit.control.communication"].browse(res_ids)

        communications_streams = super()._render_qweb_pdf_prepare_streams(
            self.env["ir.actions.report"]._get_report_from_name(
                credit_control_communication_report_name
            ),
            data,
            res_ids=communications.ids,
        )

        for com_id, com_streams in communications_streams.items():
            collected_streams[com_id] = [com_streams["stream"]]

        for communication in communications:
            dunning_fees_qr_amounts = {}
            for cr_line in communication.credit_control_line_ids:
                if not cr_line.move_line_id:
                    continue

                invoice = cr_line.invoice_id
                dunning_fees_qr_amounts[invoice.id] = cr_line.balance_due_total

            # generate QR slips for each communication as the QR report doesn't
            # include valid outlines to split the QRs for each communication afterwards
            invoice_ids = list(dunning_fees_qr_amounts.keys())
            qr_streams = super(
                Report,
                self.with_context(
                    active_ids=invoice_ids,
                    qr_dunning_fees_amounts=dunning_fees_qr_amounts,
                ),
            )._render_qweb_pdf_prepare_streams(
                "l10n_ch.qr_report_main", data, res_ids=invoice_ids
            )
            qr_streams_to_merge = [
                x["stream"] for x in qr_streams.values() if x["stream"]
            ]
            # attach QR reports to related communication report
            collected_streams[communication.id].extend(qr_streams_to_merge)

        # merge streams by communication
        for com_id, streams_to_merge in collected_streams.items():
            result_stream = io.BytesIO()
            with self._merge_pdfs(streams_to_merge) as pdf_merged_stream:
                # Write result stream in a new buffer because the result is added to the array
                #  passed as argument and we want to close streams in this array
                result_stream.write(pdf_merged_stream.getvalue())

            for stream in streams_to_merge:
                stream.close()

            collected_streams[com_id] = {"stream": result_stream, "attachment": None}

        return collected_streams
