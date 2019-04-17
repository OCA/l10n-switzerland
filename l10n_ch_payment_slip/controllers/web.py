# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo.models import _
from odoo.addons.web.controllers import main as report
from odoo.http import content_disposition, request, route


class ReportController(report.ReportController):
    @route()
    def report_routes(self, reportname, docids=None, converter=None, **data):
        if converter == "reportlab-pdf":
            report_slip = request.env.ref(
                'l10n_ch_payment_slip.one_slip_per_page_from_invoice')
            filename = ''
            invoice_id = []
            if docids:
                invoice_id = [int(i) for i in docids.split(',')]
                filename = ''.join([
                    _('ISR'),
                    '_multiple_invoices' if len(invoice_id) > 1
                    else '{0:05d}'.format(invoice_id[0]),
                    '.pdf'
                ])
            data, format_report = report_slip.render(invoice_id)
            pdfhttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', content_disposition(filename)),
                ('Content-Length', len(data)),
            ]
            return request.make_response(data, headers=pdfhttpheaders)
        return super(ReportController, self).report_routes(
            reportname, docids, converter, **data)
