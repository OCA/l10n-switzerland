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
from openerp import api, models
from openerp.report import render_report


class InvoiceBVRFromInvoice(models.AbstractModel):
    _name = 'report.invoice_and_one_slip_per_page_from_invoice'


class ExtendedReport(models.Model):

    _inherit = 'report'

    def _compute_documents_list(self, cr, uid, invoice_ids,
                                report_name=None, context=None):
        slip_model = self.pool['l10n_ch.payment_slip']
        invoice_model = self.pool['account.invoice']
        for inv in invoice_model.browse(cr, uid, invoice_ids, context=context):
            data, format = render_report(
                cr,
                uid,
                [inv.id],
                'account.report_invoice',
                {},
                context=context,
            )
            yield data
            slips = slip_model.compute_pay_slips_from_invoices(
                cr,
                uid,
                inv,
                context=context
            )
            for slip in slips:
                yield slip._draw_payment_slip(a4=True,
                                              b64=False,
                                              report_name=report_name,
                                              out_format='PDF')

    @api.v7
    def _generate_inv_and_one_slip_per_page_from_invoice_pdf(
            self, cr, uid, ids, report_name=None, context=None):
        """Generate invoice with payment slip PDF(s) on separate page
        from report model.
        PDF are merged in memory or on
        file system based on company settings

        :return: the generated PDF content
        """
        user_model = self.pool['res.users']
        company = user_model.browse(cr, uid, uid, context=context).company_id
        docs = self._compute_documents_list(cr, uid, ids,
                                            report_name=report_name,
                                            context=context)
        if company.merge_mode == 'in_memory':
            return self.merge_pdf_in_memory(docs)
        return self.merge_pdf_on_disk(docs)

    @api.v7
    def get_pdf(self, cr, uid, ids, report_name, html=None, data=None,
                context=None):
        if report_name == 'invoice_and_one_slip_per_page_from_invoice':
            return self._generate_inv_and_one_slip_per_page_from_invoice_pdf(
                cr,
                uid,
                ids,
                report_name=report_name,
                context=context
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
