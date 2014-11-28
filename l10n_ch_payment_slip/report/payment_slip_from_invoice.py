# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import StringIO
import pyPdf
from openerp import api, models


class BVRFromInvoice(models.AbstractModel):
    _name = 'report.one_slip_per_page_from_invoice'


class ExtendedReport(models.Model):

    _inherit = 'report'

    def merge_pdf_in_memory(self, docs):
        streams = []
        writer = pyPdf.PdfFileWriter()
        for doc in docs:
            current_buff = StringIO.StringIO()
            streams.append(current_buff)
            current_buff.write(
                doc._draw_payment_slip(a4=True, b64=False,
                                       out_format='PDF')
            )
            current_buff.seek(0)
            reader = pyPdf.PdfFileReader(current_buff)
            for page in xrange(reader.getNumPages()):
                writer.addPage(reader.getPage(page))
        buff = StringIO.StringIO()
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

    @api.v7
    def get_pdf(self, cr, uid, ids, report_name, html=None, data=None,
                context=None):
        if report_name == 'one_slip_per_page_from_invoice':
            slip_model = self.pool['l10n_ch.payment_slip']
            docs = slip_model.compute_pay_slips_from_invoices(
                cr,
                uid,
                self.pool['account.invoice'].browse(cr,
                                                    uid,
                                                    ids,
                                                    context=context),
                context=context
            )
            if len(docs) == 1:
                return docs[0]._draw_payment_slip(a4=True, b64=False,
                                                  out_format='PDF')
            else:
                # Faster than self._merge_pdf but uses more memory
                return self.merge_pdf_in_memory(docs)
        else:
            return super(ExtendedReport, self).get_pdf(
                cr, uid, ids, report_name,
                html=html, data=data, context=context
            )
