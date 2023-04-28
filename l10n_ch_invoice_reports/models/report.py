# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import io
import logging
from collections import OrderedDict
from io import BytesIO

import PyPDF2

from odoo import models

_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def merge_pdf_in_memory(self, docs):
        streams = []
        writer = PyPDF2.PdfFileWriter()
        for doc in docs:
            if doc:
                current_buff = BytesIO()
                streams.append(current_buff)
                current_buff.write(doc.read())
                current_buff.seek(0)
                reader = PyPDF2.PdfFileReader(current_buff)
                for page in range(reader.getNumPages()):
                    writer.addPage(reader.getPage(page))
            else:
                writer.addBlankPage()
        buff = BytesIO()
        try:
            # The writer close the reader file here
            writer.write(buff)
            return buff.getvalue()
        except IOError:
            raise
        finally:
            buff.close()
            for stream in streams:
                stream.close()

    def _get_pdf_content(self, res_ids=None, data=None):
        context = dict(self.env.context)
        html = self.with_context(context)._render_qweb_html(res_ids, data=data)[0]
        html = html.decode("utf-8")
        bodies, _, header, footer, specific_paperformat_args = self.with_context(
            context
        )._prepare_html(html)
        pdf_content = self._run_wkhtmltopdf(
            bodies,
            header=header,
            footer=footer,
            landscape=context.get("landscape"),
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=context.get("set_viewport_size"),
        )
        return pdf_content

    def _render_qweb_pdf(self, res_ids=None, data=None):
        reports = ["l10n_ch_invoice_reports.account_move_payment_report"]
        if self.report_name not in reports or not res_ids:
            return super()._render_qweb_pdf(res_ids, data)

        inv_report = self._get_report_from_name("account.report_invoice")
        qr_report = self._get_report_from_name("l10n_ch.qr_report_main")

        # Start Block - The following comes from super _render_qweb_pdf
        self_sudo = self.sudo()
        save_in_attachment = OrderedDict()
        # Maps the streams in `save_in_attachment` back to the records they came from
        stream_record = dict()
        if res_ids:
            # Dispatch the records by ones having an attachment and ones requesting a call to
            # wkhtmltopdf.
            Model = self.env[self_sudo.model]
            record_ids = Model.browse(res_ids)
            wk_record_ids = Model
            if self_sudo.attachment:
                for record_id in record_ids:
                    attachment = self_sudo.retrieve_attachment(record_id)
                    if attachment:
                        stream = self_sudo._retrieve_stream_from_attachment(attachment)
                        save_in_attachment[record_id.id] = stream
                        stream_record[stream] = record_id
                    if not self_sudo.attachment_use or not attachment:
                        wk_record_ids += record_id
            else:
                wk_record_ids = record_ids
            res_ids = wk_record_ids.ids

        # A call to wkhtmltopdf is mandatory in 2 cases:
        # - The report is not linked to a record.
        # - The report is not fully present in attachments.
        if save_in_attachment and not res_ids:
            _logger.info("The PDF report has been generated from attachments.")
            self._raise_on_unreadable_pdfs(save_in_attachment.values(), stream_record)
            return self_sudo._post_pdf(save_in_attachment), "pdf"
        # End block

        io_list = []
        for inv in self.env["account.move"].browse(res_ids):
            invoice_pdf = inv_report._get_pdf_content(inv.ids, data)
            io_list.append(io.BytesIO(invoice_pdf))
            if inv.company_id.print_qr_invoice:
                qr_pdf = qr_report._get_pdf_content(inv.ids, data)
                io_list.append(io.BytesIO(qr_pdf))
            pdf = self.merge_pdf_in_memory(io_list)
            for io_file in io_list:
                io_file.close()

            _logger.info(
                "The PDF report has been generated for model: %s, records %s."
                % (self_sudo.model, str(res_ids))
            )
            return (
                self_sudo._post_pdf(
                    save_in_attachment, pdf_content=pdf, res_ids=res_ids
                ),
                "pdf",
            )
