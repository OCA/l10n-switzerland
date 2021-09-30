# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import io
from io import BytesIO

import PyPDF2

from odoo import models


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

    def _render_qweb_pdf(self, res_ids=None, data=None):
        reports = [
            "l10n_ch_invoice_reports.invoice_isr_report_main",
            "l10n_ch_invoice_reports.invoice_qr_report_main",
            "l10n_ch_invoice_reports.invoice_qr_isr_report_main",
        ]
        if self.report_name not in reports or not res_ids:
            return super()._render_qweb_pdf(res_ids, data)

        inv_report = self._get_report_from_name("account.report_invoice")
        invoice_pdf, _ = inv_report._render_qweb_pdf(res_ids, data)
        invoice_pdf_io = io.BytesIO(invoice_pdf)

        isr_report = self._get_report_from_name("l10n_ch.isr_report_main")
        isr_pdf, _ = isr_report._render_qweb_pdf(res_ids, data)
        isr_pdf_io = io.BytesIO(isr_pdf)

        qr_report = self._get_report_from_name("l10n_ch.qr_report_main")
        qr_pdf, _ = qr_report._render_qweb_pdf(res_ids, data)
        qr_pdf_io = io.BytesIO(qr_pdf)

        pdf = False
        if self.report_name == reports[0]:
            pdf = self.merge_pdf_in_memory([invoice_pdf_io, isr_pdf_io])
        elif self.report_name == reports[1]:
            pdf = self.merge_pdf_in_memory([invoice_pdf_io, qr_pdf_io])
        else:
            pdf = self.merge_pdf_in_memory([invoice_pdf_io, isr_pdf_io, qr_pdf_io])
        invoice_pdf_io.close()
        isr_pdf_io.close()
        qr_pdf_io.close()
        return (pdf, "pdf")
