# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
#    Donors: Hasa Sàrl, Open Net Sàrl and Prisme Solutions Informatique SA
#    Ported to v8.0 by Agile Business Group <http://www.agilebg.com>
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
from openerp import models, fields


# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import logging
import time

from openerp.osv import fields, osv

_logger = logging.getLogger(__name__)

class payment_mode(osv.osv):
    _name= 'payment.mode'
    _description= 'Payment Mode'
    _columns = {
        'name': fields.char('Name', required=True, help='Mode of Payment'),
        'bank_id': fields.many2one('res.partner.bank', "Bank account",
            required=True,help='Bank Account for the Payment Mode'),
        'journal_id': fields.many2one('account.journal', 'Journal', required=True,
            domain=[('type', 'in', ('bank','cash'))], help='Bank or Cash Journal for the Payment Mode'),
        'company_id': fields.many2one('res.company', 'Company',required=True),
        'partner_id':fields.related('company_id','partner_id',type='many2one',relation='res.partner',string='Partner',store=True,),

    }
    _defaults = {
        'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id
    }

    def suitable_bank_types(self, cr, uid, payment_code=None, context=None):
        """Return the codes of the bank type that are suitable
        for the given payment type code"""
        if not payment_code:
            return []
        cr.execute(""" SELECT pb.state
            FROM res_partner_bank pb
            JOIN payment_mode pm ON (pm.bank_id = pb.id)
            WHERE pm.id = %s """, [payment_code])
        return [x[0] for x in cr.fetchall()]

    def onchange_company_id (self, cr, uid, ids, company_id=False, context=None):
        result = {}
        if company_id:
            partner_id = self.pool.get('res.company').browse(cr, uid, company_id, context=context).partner_id.id
            result['partner_id'] = partner_id
        return {'value': result}



class payment_register(osv.osv):
    _name = 'payment.register'
    _description = 'Payment Register'
    _rec_name = 'reference'
    _order = 'id desc'

    #dead code
    def get_wizard(self, type):
        _logger.warning("No wizard found for the payment type '%s'.", type)
        return None

    def _total(self, cursor, user, ids, name, args, context=None):
        if not ids:
            return {}
        res = {}
        for order in self.browse(cursor, user, ids, context=context):
            if order.line_ids:
                res[order.id] = reduce(lambda x, y: x + y.amount, order.line_ids, 0.0)
            else:
                res[order.id] = 0.0
        return res

    _columns = {
        'date_scheduled': fields.date('Scheduled Date', states={'done':[('readonly', True)]}, help='Select a date if you have chosen Preferred Date to be fixed.'),
        'reference': fields.char('Reference', required=1, states={'done': [('readonly', True)]}, copy=False),
        'mode': fields.many2one('payment.mode', 'Payment Mode', select=True, required=1, states={'done': [('readonly', True)]}, help='Select the Payment Mode to be applied.'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('cancel', 'Cancelled'),
            ('open', 'Confirmed'),
            ('done', 'Done')], 'Status', select=True, copy=False,
            help='When an order is placed the status is \'Draft\'.\n Once the bank is confirmed the status is set to \'Confirmed\'.\n Then the order is paid the status is \'Done\'.'),
        'line_ids': fields.one2many('payment.register.line', 'order_id', 'Payment lines', states={'done': [('readonly', True)]}),
        'total': fields.function(_total, string="Total", type='float'),
        'user_id': fields.many2one('res.users', 'Responsible', required=True, states={'done': [('readonly', True)]}),
        'date_prefered': fields.selection([
            ('now', 'Directly'),
            ('due', 'Due date'),
            ('fixed', 'Fixed date')
            ], "Preferred Date", change_default=True, required=True, states={'done': [('readonly', True)]}, help="Choose an option for the Payment Order:'Fixed' stands for a date specified by you.'Directly' stands for the direct execution.'Due date' stands for the scheduled date of execution."),
        'date_created': fields.date('Creation Date', readonly=True),
        'date_done': fields.date('Execution Date', readonly=True),
        'company_id': fields.related('mode', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'entries_test': fields.many2many('account.move.line', 'test_line_pay_rel', 'pay_id', 'line_id')
    }

    _defaults = {
        'user_id': lambda self,cr,uid,context: uid,
        'state': 'draft',
        'date_prefered': 'due',
        'date_created': lambda *a: time.strftime('%Y-%m-%d'),
        'reference': lambda self,cr,uid,context: self.pool.get('ir.sequence').get(cr, uid, 'payment.order'),
    }

    def set_to_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'draft'})
        self.create_workflow(cr, uid, ids)
        return True

    def action_open(self, cr, uid, ids, *args):
        ir_seq_obj = self.pool.get('ir.sequence')

        for order in self.read(cr, uid, ids, ['reference']):
            if not order['reference']:
                reference = ir_seq_obj.get(cr, uid, 'payment.order')
                self.write(cr, uid, order['id'], {'reference':reference})
        return True

    def set_done(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'date_done': time.strftime('%Y-%m-%d')})
        self.signal_workflow(cr, uid, ids, 'done')
        return True

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        payment_line_obj = self.pool.get('payment.register.line')
        payment_line_ids = []

        if (vals.get('date_prefered', False) == 'fixed' and not vals.get('date_scheduled', False)) or vals.get('date_scheduled', False):
            for order in self.browse(cr, uid, ids, context=context):
                for line in order.line_ids:
                    payment_line_ids.append(line.id)
            payment_line_obj.write(cr, uid, payment_line_ids, {'date': vals.get('date_scheduled', False)}, context=context)
        elif vals.get('date_prefered', False) == 'due':
            vals.update({'date_scheduled': False})
            for order in self.browse(cr, uid, ids, context=context):
                for line in order.line_ids:
                    payment_line_obj.write(cr, uid, [line.id], {'date': line.ml_maturity_date}, context=context)
        elif vals.get('date_prefered', False) == 'now':
            vals.update({'date_scheduled': False})
            for order in self.browse(cr, uid, ids, context=context):
                for line in order.line_ids:
                    payment_line_ids.append(line.id)
            payment_line_obj.write(cr, uid, payment_line_ids, {'date': False}, context=context)
        return super(payment_register, self).write(cr, uid, ids, vals, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

