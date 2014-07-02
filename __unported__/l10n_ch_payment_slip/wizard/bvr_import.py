# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
#    Financial contributors: Hasa SA, Open Net SA,
#                            Prisme Solutions Informatique SA, Quod SA
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
import base64
import time
import re

from openerp.tools.translate import _
from openerp.osv.orm import TransientModel, fields
from openerp.osv.osv import except_osv
from openerp.tools import mod10r

REF = re.compile('[^0-9]')


class BvrImporterWizard(TransientModel):

    _name = 'bvr.import.wizard'

    _columns = {'file': fields.binary('BVR File')}

    def _reconstruct_invoice_ref(self, cursor, user, reference, context=None):
        """Try to get correct invoice/invoice line form ESV/BVR reference"""
        id_invoice = False
        # On fait d'abord une recherche sur toutes les factures
        # we now search for an invoice
        user_obj = self.pool['res.users']
        user_current = user_obj.browse(cursor, user, user)

        cursor.execute("SELECT inv.id, inv.number from account_invoice "
                       "AS inv where inv.company_id = %s and type='out_invoice'",
                       (user_current.company_id.id,))
        result_invoice = cursor.fetchall()
        for inv_id, inv_name in result_invoice:
            inv_name = REF.sub('0', str(inv_name))
            if inv_name == reference:
                id_invoice = inv_id
                break
        if id_invoice:
            cursor.execute('SELECT l.id'
                           '  FROM account_move_line l, account_invoice i'
                           '    WHERE l.move_id = i.move_id AND l.reconcile_id is NULL  '
                           '    AND i.id IN %s', (tuple([id_invoice]),))
            inv_line = []
            for id_line in cursor.fetchall():
                inv_line.append(id_line[0])
            return inv_line
        else:
            return []

    def _parse_lines(self, cursor, uid, inlines, context=None):
        """Parses raw v11 line and populate records list with dict"""
        records = []
        total_amount = 0
        total_cost = 0
        find_total = False
        for lines in inlines:
            if not lines:  # manage new line at end of file
                continue
            (line, lines) = (lines[:128], lines[128:])
            record = {}
            if line[0:3] in ('999', '995'):
                if find_total:
                    raise except_osv(_('Error'),
                                     _('Too much total record found!'))
                find_total = True
                if lines:
                    raise except_osv(_('Error'),
                                     _('Record found after total record!'))
                amount = float(line[39:49]) + (float(line[49:51]) / 100)
                cost = float(line[69:76]) + (float(line[76:78]) / 100)
                if line[2] == '5':
                    amount *= -1
                    cost *= -1

                if round(amount - total_amount, 2) >= 0.01 \
                        or round(cost - total_cost, 2) >= 0.01:
                    raise except_osv(_('Error'),
                                     _('Total record different from the computed!'))
                if int(line[51:63]) != len(records):
                    raise except_osv(_('Error'),
                                     _('Number record different from the computed!'))
            else:
                record = {
                    'reference': line[12:39],
                    'amount': float(line[39:47]) + (float(line[47:49]) / 100),
                    'date': time.strftime('%Y-%m-%d', time.strptime(line[65:71], '%y%m%d')),
                    'cost': float(line[96:98]) + (float(line[98:100]) / 100),
                }

                if record['reference'] != mod10r(record['reference'][:-1]):
                    raise except_osv(_('Error'),
                                     _('Recursive mod10 is invalid for reference: %s') % record['reference'])

                if line[2] == '5':
                    record['amount'] *= -1
                    record['cost'] *= -1
                total_amount += record['amount']
                total_cost += record['cost']
                records.append(record)
        return records

    #deprecated
    def _create_voucher_from_record(self, cursor, uid, record,
                                    statement, line_ids, context=None):
        """Create a voucher with voucher line"""
        context.update({'move_line_ids': line_ids})
        voucher_obj = self.pool.get('account.voucher')
        move_line_obj = self.pool.get('account.move.line')
        voucher_line_obj = self.pool.get('account.voucher.line')
        line = move_line_obj.browse(cursor, uid, line_ids[0])
        partner_id = line.partner_id and line.partner_id.id or False
        if not partner_id:
            return False
        move_id = line.move_id.id
        result = voucher_obj.onchange_partner_id(cursor, uid, [],
                                                 partner_id,
                                                 statement.journal_id.id,
                                                 abs(record['amount']),
                                                 statement.currency.id,
                                                 'receipt',
                                                 statement.date,
                                                 context=context)
        voucher_res = {'type': 'receipt',
                       'name': record['reference'],
                       'partner_id': partner_id,
                       'journal_id': statement.journal_id.id,
                       'account_id': result.get('account_id', statement.journal_id.default_credit_account_id.id),
                       'company_id': statement.company_id.id,
                       'currency_id': statement.currency.id,
                       'date': record['date'] or time.strftime('%Y-%m-%d'),
                       'amount': abs(record['amount']),
                       'period_id': statement.period_id.id
                       }
        voucher_id = voucher_obj.create(cursor, uid, voucher_res, context=context)

        voucher_line_dict = False
        if result['value']['line_cr_ids']:
            for line_dict in result['value']['line_cr_ids']:
                move_line = move_line_obj.browse(cursor, uid, line_dict['move_line_id'], context)
                if move_id == move_line.move_id.id:
                    voucher_line_dict = line_dict
        if voucher_line_dict:
            voucher_line_dict.update({'voucher_id': voucher_id})
            voucher_line_obj.create(cursor, uid, voucher_line_dict, context=context)
        return voucher_id

    def _get_account(self, cursor, uid, line_ids, record, context=None):
        """Get account from move line or from property"""
        property_obj = self.pool.get('ir.property')
        move_line_obj = self.pool.get('account.move.line')
        account_id = False
        if line_ids:
            for line in move_line_obj.browse(cursor, uid, line_ids, context=context):
                return line.account_id.id
        if not account_id and not line_ids:
            name = "property_account_receivable"
            if record['amount'] < 0:
                name = "property_account_payable"
            account_id = property_obj.get(cursor, uid, name, 'res.partner', context=context).id
            if not account_id:
                raise except_osv(_('Error'),
                                 _('The properties account payable account receivable are not set'))
        return account_id

    def _prepare_line_vals(self, cursor, uid, statement, record,
                           voucher_enabled, context=None):
        # Remove the 11 first char because it can be adherent number
        # TODO check if 11 is the right number
        move_line_obj = self.pool.get('account.move.line')
        reference = record['reference']
        values = {'name': '/',
                  'date': record['date'],
                  'amount': record['amount'],
                  'ref': reference,
                  'type': (record['amount'] >= 0 and 'customer') or 'supplier',
                  'statement_id': statement.id,
                  }
        line_ids = move_line_obj.search(cursor, uid,
                                        [('ref', '=', reference),
                                         ('reconcile_id', '=', False),
                                         ('account_id.type', 'in', ['receivable', 'payable']),
                                         ('journal_id.type', '=', 'sale')],
                                        order='date desc', context=context)
        #for multiple payments
        if not line_ids:
            line_ids = move_line_obj.search(cursor, uid,
                                            [('transaction_ref', '=', reference),
                                             ('reconcile_id', '=', False),
                                             ('account_id.type', 'in', ['receivable', 'payable']),
                                             ('journal_id.type', '=', 'sale')],
                                            order='date desc', context=context)
        if not line_ids:
            line_ids = self._reconstruct_invoice_ref(cursor, uid, reference, None)
        if line_ids and voucher_enabled:
            values['voucher_id'] = self._create_voucher_from_record(cursor, uid, record,
                                                                    statement, line_ids,
                                                                    context=context)
        account_id = self._get_account(cursor, uid, line_ids,
                                       record, context=context)
        values['account_id'] = account_id
        if line_ids:
            line = move_line_obj.browse(cursor, uid, line_ids[0])
            partner_id = line.partner_id.id
            values['name'] = line.invoice and (_('Inv. no ') + line.invoice.number) or values['name']
            values['partner_id'] = partner_id
        return values

    def import_v11(self, cursor, uid, ids, data, context=None):
        """Import v11 file and transfor it into statement lines"""
        if context is None: context = {}
        module_obj = self.pool['ir.module.module']
        voucher_enabled = module_obj.search(cursor, uid, [('name', '=', 'account_voucher'),
                                                          ('state', '=', 'installed')])
        # if module installed we check ir.config_parameter to force disable of voucher
        if voucher_enabled:
            para = self.pool['ir.config_parameter'].get_param(cursor,
                                                              uid,
                                                              'l10n_ch_payment_slip_voucher_disable',
                                                              default = '0')
            if para.lower() not in ['0', 'false']: # if voucher is disabled
                voucher_enabled = False
        statement_line_obj = self.pool.get('account.bank.statement.line')
        attachment_obj = self.pool.get('ir.attachment')
        statement_obj = self.pool.get('account.bank.statement')
        file = data['form']['file']
        if not file:
            raise except_osv(_('UserError'),
                             _('Please select a file first!'))
        statement_id = data['id']
        lines = base64.decodestring(file).split("\n")
        records = self._parse_lines(cursor, uid, lines, context=context)

        statement = statement_obj.browse(cursor, uid, statement_id, context=context)
        for record in records:
            values = self._prepare_line_vals(cursor, uid, statement,
                                             record, voucher_enabled,
                                             context=context)
            statement_line_obj.create(cursor, uid, values, context=context)
        attachment_obj.create(cursor, uid,
                              {'name': 'BVR %s' % time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime()),
                               'datas': file,
                               'datas_fname': 'BVR %s.txt' % time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime()),
                               'res_model': 'account.bank.statement',
                               'res_id': statement_id,
                               },
                              context=context)

        return {}

    def import_bvr(self, cursor, uid, ids, context=None):
        data = {}
        if context is None: context = {}
        active_ids = context.get('active_ids', [])
        active_id = context.get('active_id', False)
        data['form'] = {}
        data['ids'] = active_ids
        data['id'] = active_id
        data['form']['file'] = ''
        res = self.read(cursor, uid, ids[0], ['file'])
        if res:
            data['form']['file'] = res['file']
        self.import_v11(cursor, uid, ids, data, context=context)
        return {}



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
