# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from io import BytesIO

import PyPDF2

from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def merge_pdf_in_memory(self, docs):
        writer = PyPDF2.PdfFileWriter()
        streams = []
        buff = BytesIO()
        for doc in docs:
            if not doc:
                writer.addBlankPage()
                continue

            # If doc is raw bytes, wrap once in BytesIO
            if isinstance(doc, (bytes, bytearray)):
                stream = BytesIO(doc)
                streams.append(stream)
                reader = PyPDF2.PdfFileReader(stream)
            elif hasattr(doc, "read"):
                doc.seek(0)
                reader = PyPDF2.PdfFileReader(doc)
            else:
                # Unknown type: coerce to bytes then wrap
                stream = BytesIO(bytes(doc))
                streams.append(stream)
                reader = PyPDF2.PdfFileReader(stream)

            for page in range(reader.getNumPages()):
                writer.addPage(reader.getPage(page))
        try:
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
            "l10n_ch_invoice_reports.account_move_payment_report",
        ]
        if self.report_name not in reports or not res_ids:
            return super()._render_qweb_pdf(res_ids, data)

        inv_report = self._get_report_from_name("account.report_invoice")
        qr_report = self._get_report_from_name("l10n_ch.qr_report_main")
        isr_report = self._get_report_from_name("l10n_ch.isr_report_main")

        io_list = []
        moves = self.env["account.move"].browse(res_ids)
        # read returns dicts with 'id' and 'company_id' tuples in order
        # to avoid per-record browse for company fields
        moves_data = moves.read(["company_id"]) if moves else []
        company_ids = {m["company_id"][0] for m in moves_data if m.get("company_id")}
        companies = {}
        if company_ids:
            for c in (
                self.env["res.company"]
                .browse(list(company_ids))
                .read(["print_qr_invoice", "print_isr_invoice"])
            ):
                companies[c["id"]] = c

        for inv in moves:
            invoice_pdf, _ = inv_report._render_qweb_pdf(inv.id, data)
            io_list.append(invoice_pdf)

            comp = companies.get(inv.company_id.id, {})
            if comp.get("print_qr_invoice"):
                qr_pdf, _ = qr_report._render_qweb_pdf(inv.id, data)
                io_list.append(qr_pdf)

            if comp.get("print_isr_invoice"):
                isr_pdf, _ = isr_report._render_qweb_pdf(inv.id, data)
                io_list.append(isr_pdf)

        # io_list contains raw bytes and/or file-like objects; merge handles both
        pdf = self.merge_pdf_in_memory(io_list)
        return (pdf, "pdf")
