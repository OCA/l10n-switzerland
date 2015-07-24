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
from openerp import models


class BVRFromInvoice(models.AbstractModel):
    _name = 'report.one_slip_per_page_from_invoice'


class ExtendedReport(models.Model):

    _inherit = 'report'

    def _generate_one_slip_per_page_from_invoice_pdf(self, cr, uid, ids,
                                                     report_name=None,
                                                     context=None):
        """Generate payment slip PDF(s) from report model.
        If there is many pdf they are merged in memory or on
        file system based on company settings

        :return: the generated PDF content
        """
        user_model = self.pool['res.users']
        slip_model = self.pool['l10n_ch.payment_slip']
        invoice_model = self.pool['account.invoice']
        company = user_model.browse(cr, uid, uid, context=context).company_id
        invoice = invoice_model.browse(cr, uid, ids, context=context)
        docs = slip_model.compute_pay_slips_from_invoices(
            cr,
            uid,
            invoice,
            context=context
        )
        if len(docs) == 1:
            return docs[0]._draw_payment_slip(a4=True,
                                              b64=False,
                                              report_name=report_name,
                                              out_format='PDF')
        else:
            pdfs = (x._draw_payment_slip(a4=True, b64=False, out_format='PDF',
                                         report_name=report_name)
                    for x in docs)
            if company.merge_mode == 'in_memory':
                return self.merge_pdf_in_memory(pdfs)
            return self.merge_pdf_on_disk(pdfs)

    def get_pdf(self, cr, uid, ids, report_name, html=None, data=None,
                context=None):
        if report_name == 'one_slip_per_page_from_invoice':
            return self._generate_one_slip_per_page_from_invoice_pdf(
                cr,
                uid,
                ids,
                context=context,
                report_name=report_name,
            )
        else:
            return super(ExtendedReport, self).get_pdf(
                cr,
                uid,
                ids,
                report_name,
                html=html,
                data=data,
                context=context
            )
