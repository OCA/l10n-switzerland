# -*- coding: utf-8 -*-
# © 2012-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models
from openerp.addons.base.ir.ir_actions import ir_actions_report_xml as root


class IrActionsReportXMLReportlab(models.Model):

    _inherit = 'ir.actions.report.xml'

    def __init__(self, cr, uid):
        """Old school hack to extend selection fields"""
        super(IrActionsReportXMLReportlab, self).__init__(cr, uid)
        if not any(x for x in root._columns['report_type'].selection
                   if x[0] == 'reportlab-pdf'):
            root._columns['report_type'].selection.append(
                ('reportlab-pdf', 'Report renderer')
            )

    def _lookup_report(self, cr, name):
        cr.execute("SELECT * FROM ir_act_report_xml WHERE report_name=%s",
                   (name,))
        report = cr.dictfetchone()
        if report and report['report_type'] == 'reportlab-pdf':
            return report['report_name']
        else:
            return super(IrActionsReportXMLReportlab, self)._lookup_report(
                cr,
                name
            )

    def render_report(self, cr, uid, res_ids, name, data, context=None):
        """
        Override to work with real pdf in testing and not html
        as we use reportlab as renderer
        """
        if context is None:
            context = {}
        if context.get('force_pdf'):
            new_report = self._lookup_report(cr, name)
            if isinstance(new_report, (str, unicode)):
                return self.pool['report'].get_pdf(
                    cr,
                    uid,
                    res_ids,
                    new_report,
                    data=data,
                    context=context
                ), 'pdf'
        return super(IrActionsReportXMLReportlab, self).render_report(
            cr,
            uid,
            res_ids,
            name,
            data,
            context=context
        )
