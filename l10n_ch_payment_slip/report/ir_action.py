# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2015 Camptocamp SA
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
from openerp.osv import orm
from openerp.addons.base.ir.ir_actions import ir_actions_report_xml as root


class ir_actions_report_xml_reportlab(orm.Model):

    _inherit = 'ir.actions.report.xml'

    def __init__(self, cr, uid):
        """Old school hack to extend selection fields"""
        super(ir_actions_report_xml_reportlab, self).__init__(cr, uid)
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
            return super(ir_actions_report_xml_reportlab, self)._lookup_report(
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
        return super(ir_actions_report_xml_reportlab, self).render_report(
            cr,
            uid,
            res_ids,
            name,
            data,
            context=context
        )
