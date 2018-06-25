# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo.addons.web.controllers import main as report
from odoo.http import request, route


class ReportController(report.ReportController):
    @route()
    def report_routes(self, reportname, docids=None, converter=None, **data):
        if converter == "reportlab_pdf":
            report_slip = request.env.ref(
                'l10n_ch_payment_slip.one_slip_per_page_from_invoice')
            if docids:
                docids = [int(i) for i in docids.split(',')]
            data, format = report_slip.render(docids)
            pdfhttpheaders = [
                    ('Content-Type', 'application/pdf'),
                    ('Content-Disposition', 'attachment'),
                    ('Content-Length', len(data)),
            ]
            return request.make_response(data, headers=pdfhttpheaders)
        return super(ReportController, self).report_routes(
            reportname, docids, converter, **data)
