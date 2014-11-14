# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville. Copyright 2013 Camptocamp SA
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
import netsvc
from openerp.report import report_sxw
from openerp.osv import orm
from openerp.tools.translate import _
from l10n_ch_payment_slip.report import multi_report_webkit_html


class CreditCommunication(orm.TransientModel):

    """Shell class used to provide a base model to email template
       and reporting.
       Il use this approche in version 7 a browse record will
       exist even if not saved"""
    _inherit = "credit.control.communication"

    def _generate_report_bvr(self, cr, uid, line_ids, context=None):
        """Will generate a report by inserting mako template
           of Multiple BVR Report"""
        service = netsvc.LocalService(
            'report.invoice_bvr_webkit_multi_credit_control'
        )
        result, format = service.create(cr, uid, line_ids, {}, {})
        return result


class MultiBvrWebKitParserCreditControl(
        multi_report_webkit_html.L10nCHReportWebkitHtmlMulti):

    """We define a new parser because this report take move line
       In parameter insted of an invoice, so the function get_obj_reference
       return directly ids"""

    def check_currency(self, line, company_curr, swiss_curr):

        curr = line.currency_id if line.currency_id else company_curr
        if curr != swiss_curr:
            raise orm.except_orm(
                _('ERROR'),
                _('BVR only support CHF currency')
            )
        return True

    def get_company_currency(self):
        cmp_model = self.pool['res.company']
        c_id = cmp_model._company_default_get(self.cr, self.uid,
                                              'res.currency')
        comp = cmp_model.browse(self.cr, self.uid, c_id)
        return comp.currency_id

    def get_swiss_currency(self):
        return self.pool['ir.model.data'].get_object(
            self.cr,
            self.uid,
            'base',
            'CHF'
        )

    def set_context(self, objects, data, ids, report_type=None):
        new_objects = []
        new_ids = []
        company_currency = self.get_company_currency()
        swiss_currency = self.get_swiss_currency()
        for credit_line in objects:
            self.check_currency(credit_line, company_currency, swiss_currency)
            ml = credit_line.move_line_id
            ml.bvr_dunning_fees = credit_line.dunning_fees_amount
            new_ids.append(ml.id)
            new_objects.append(ml)
        self._check(new_ids)
        # We do not want to call L10nCHReportWebkitHtmlMulti set_context
        return report_sxw.rml_parse.set_context(
            self,
            new_objects,
            new_ids,
            ids,
            report_type=report_type
        )

report_sxw.report_sxw('report.invoice_bvr_webkit_multi_credit_control',
                      'credit.control.line',
                      'addons/l10n_ch_payment_slip/report/multi_bvr.mako',
                      parser=MultiBvrWebKitParserCreditControl)
