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
from openerp.osv.orm import TransientModel
from l10n_ch_payment_slip.report import webkit_parser
from l10n_ch_payment_slip.report import multi_report_webkit_html


class CreditCommunication(TransientModel):
    """Shell class used to provide a base model to email template
       and reporting.
       Il use this approche in version 7 a browse record will
       exist even if not saved"""
    _inherit = "credit.control.communication"

    def _generate_report_bvr(self, cr, uid, lines, context=None):
        """Will generate a report by inserting mako template
           of Multiple BVR Report"""
        service = netsvc.LocalService('report.invoice_bvr_webkit_multi_credit_control')
        result, format = service.create(cr, uid, lines, {}, {})
        return result


class MultiBvrWebKitParserCreditControl(webkit_parser.MultiBvrWebKitParser):
    """We define a new parser because this report take move line
       In parameter insted of an invoice, so the function get_obj_reference
       return directly ids"""

    def get_obj_reference(self, cursor, uid, ids, context=None):
        return ids

MultiBvrWebKitParserCreditControl('report.invoice_bvr_webkit_multi_credit_control',
                                  'account.invoice',
                                  'addons/l10n_ch_payment_slip/report/multi_bvr.mako',
                                  parser=multi_report_webkit_html.L10nCHReportWebkitHtmlMulti)
