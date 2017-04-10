# -*- coding: utf-8 -*-
# © 2012-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class IrActionsReportXMLReportlab(models.Model):

    _inherit = 'ir.actions.report.xml'

    report_type = fields.Selection(selection_add=[('reportlab-pdf',
                                                   'Report renderer')])

    @api.model
    def _lookup_report(self, name):
        self.env.cr.execute(
            "SELECT * FROM ir_act_report_xml WHERE report_name=%s", (name,))
        report = self.env.cr.dictfetchone()
        if report and report['report_type'] == 'reportlab-pdf':
            return report['report_name']
        else:
            return super(IrActionsReportXMLReportlab, self)._lookup_report(
                name)

    @api.multi
    def render_report(self, res_ids, name, data):
        """
        Override to work with real pdf in testing and not html
        as we use reportlab as renderer
        """
        context = self._context
        if context is None:
            context = {}
        if context.get('force_pdf'):
            new_report = self._lookup_report(name)
            if isinstance(new_report, (str, unicode)):
                return self.env['report'].get_pdf(
                    res_ids,
                    new_report,
                    data=data,
                    ), 'pdf'
        return super(IrActionsReportXMLReportlab, self).render_report(
            res_ids,
            name,
            data,
            )
