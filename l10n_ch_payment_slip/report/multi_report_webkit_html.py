# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Romain Deheele. Copyright Camptocamp SA
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
import re
import time

from openerp import addons
from openerp.report import report_sxw
from openerp.osv import orm

from openerp.tools import mod10r
from openerp.tools.translate import _
from ..invoice import AccountInvoice


class L10nCHReportWebkitHtmlMulti(report_sxw.rml_parse):
    """Report that output single BVR from invoice.
    This report is deprectated and will be merged
    with multi payment term BVR report when porting to V8"""

    def __init__(self, cr, uid, name, context):
        super(L10nCHReportWebkitHtmlMulti, self).__init__(cr, uid, name,
                                                          context=context)
        self.localcontext.update({
            'time': time,
            'cr': cr,
            'uid': uid,
            'user': self.pool.get("res.users").browse(cr, uid, uid),
            'mod10r': mod10r,
            '_space': AccountInvoice._space,
            '_get_ref': self._get_ref,
            'comma_me': self.comma_me,
            'police_absolute_path': self.police_absolute_path,
            'bvr_absolute_path': self.bvr_absolute_path,
            'headheight': self.headheight,
            'amount': self.amount,
        })

    _compile_get_ref = re.compile('[^0-9]')
    _compile_comma_me = re.compile("^(-?\d+)(\d{3})")
    _compile_check_bvr = re.compile('[0-9][0-9]-[0-9]{3,6}-[0-9]')
    _compile_check_bvr_add_num = re.compile('[0-9]*$')

    def set_context(self, objects, data, ids, report_type=None):
        ml_ids = self.get_obj_reference(ids)
        self._check(ml_ids)
        objects = self.pool['account.move.line'].browse(self.cr, self.uid,
                                                        ml_ids)

        return super(L10nCHReportWebkitHtmlMulti, self).set_context(
            objects,
            data,
            ids,
            report_type=report_type
        )

    def get_obj_reference(self, ids, context=None):
        cursor, uid = self.cr, self.uid
        move_line_obj = self.pool.get('account.move.line')
        account_obj = self.pool.get('account.account')
        invoice_obj = self.pool.get('account.invoice')
        inv = invoice_obj.browse(cursor, uid, ids[0], context=context)
        tier_account_ids = account_obj.search(
            cursor, uid,
            [('type', 'in', ['receivable', 'payable'])],
            context=context)
        move_line_ids = move_line_obj.search(
            cursor, uid,
            [('move_id', '=', inv.move_id.id),
             ('account_id', 'in', tier_account_ids)],
            context=context)
        return move_line_ids

    def amount(self, move, rtype=None):
        ml_model = self.pool['account.move.line']
        return ml_model._get_bvr_amount(self.cr, self.uid, move, rtype=rtype)

    def _get_ref(self, move):
        """Get BVR reference using move related to invoice"""
        model = self.pool['account.move.line']
        return model.get_bvr_ref(self.cr, self.uid, move.id)

    def police_absolute_path(self, inner_path):
        """Will get the ocrb police absolute path"""
        path = addons.get_module_resource('l10n_ch_payment_slip', 'report', inner_path)
        return path

    def bvr_absolute_path(self):
        """Will get the ocrb police absolute path"""
        path = addons.get_module_resource('l10n_ch_payment_slip', 'report', 'bvr1.jpg')
        return path

    def headheight(self):
        report_id = self.pool['ir.actions.report.xml'].search(self.cr, self.uid,
                                                              [('name', '=', 'BVR invoice')])[0]
        report = self.pool['ir.actions.report.xml'].browse(self.cr, self.uid, report_id)
        return report.webkit_header.margin_top

    def comma_me(self, amount):
        """Fast swiss number formatting"""
        if isinstance(amount, float):
            amount = str('%.2f' % amount)
        else:
            amount = str(amount)
        orig = amount
        new = self._compile_comma_me.sub("\g<1>'\g<2>", amount)
        if orig == new:
            return new
        else:
            return self.comma_me(new)

    def _check_invoice(self, invoice_ids):
        """Check if the invoice is ready to be printed"""
        if not invoice_ids:
            invoice_ids = []
        cursor = self.cr
        invoice_obj = self.pool['account.invoice']
        ids = invoice_ids
        for invoice in invoice_obj.browse(cursor, self.uid, ids):
            invoice_name = "%s %s" % (invoice.name, invoice.number)
            if not invoice.number:
                raise orm.except_orm(
                    _('UserError'),
                    _('Your invoice should be validated to generate a BVR reference.')
                )
            if not invoice.partner_bank_id:
                raise orm.except_orm(
                    _('UserError'),
                    _('No bank specified on invoice:\n%s' % (invoice_name))
                )
            if not self._compile_check_bvr.match(
                    invoice.partner_bank_id.get_account_number() or ''):
                raise orm.except_orm(
                    _('UserError'),
                    _(('Your bank BVR number should be of the form 0X-XXX-X! '
                       'Please check your company '
                       'information for the invoice:\n%s') % (invoice_name))
                )
            adherent_num = invoice.partner_bank_id.bvr_adherent_num
            if invoice.partner_bank_id.bvr_adherent_num \
                    and not self._compile_check_bvr_add_num.match(adherent_num):
                raise orm.except_orm(
                    _('UserError'),
                    _(('Your bank BVR adherent number must contain only '
                       'digits!\nPlease check your company '
                       'information for the invoice:\n%s') % (invoice_name))
                )
        return ''

    def _check(self, move_ids):
        cursor = self.cr
        move_line_obj = self.pool['account.move.line']
        if not move_ids:
            raise orm.except_orm(
                _('UserError'),
                _('Your invoice should be validated to generate BVR reference.')
            )
        invoice_id = move_line_obj.read(cursor, self.uid, move_ids[0],
                                        ['invoice'])['invoice'][0]
        if invoice_id:
            self._check_invoice([invoice_id])

report_sxw.report_sxw('report.invoice_bvr_webkit_multi',
                      'account.invoice',
                      'l10n_ch_payment_slip/report/multi_bvr.mako',
                      parser=L10nCHReportWebkitHtmlMulti)
