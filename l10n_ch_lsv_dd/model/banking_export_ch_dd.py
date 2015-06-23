##############################################################################
#
#    Swiss localization Direct Debit module for OpenERP
#    Copyright (C) 2014 Compassion (http://www.compassion.ch)
#    @author: Cyril Sester <cyril.sester@outlook.com>
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
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.addons.decimal_precision import decimal_precision as dp

import logging
logger = logging.getLogger(__name__)


class banking_export_ch_dd(orm.Model):

    ''' Swiss Direct Debit export containing the file created
        by the appropriate wizard
    '''
    _name = 'banking.export.ch.dd'
    _rec_name = 'filename'

    def _generate_filename(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for dd_export in self.browse(cr, uid, ids, context=context):
            ref = self.pool.get('ir.sequence').next_by_code(
                cr, uid, 'l10n.banking.export.filename', context=context)

            username = self.pool.get('res.users').browse(cr, uid, uid).name
            initials = ''.join([subname[0] for subname in username.split()])
            if dd_export.type == 'LSV':
                res[dd_export.id] = 'lsv_%s_%s.lsv' % (ref, initials)
            else:
                res[dd_export.id] = 'dd_%s_%s.dd' % (ref, initials)
        return res

    _columns = {
        'payment_order_ids': fields.many2many(
            'payment.order', 'account_payment_order_ch_dd_rel',
            'banking_export_ch_dd_id', 'account_order_id',
            _('Payment Orders'), readonly=True),
        'nb_transactions': fields.integer(
            _('Number of Transactions'),
            readonly=True),
        'total_amount': fields.float(
            _('Total Amount'), readonly=True,
            digits_compute=dp.get_precision('Account')),
        'create_date': fields.datetime(_('Generation Date'), readonly=True),
        'file': fields.binary(_('Generated file'), readonly=True),
        'filename': fields.function(
            _generate_filename, type='char', size=256, string=_('Filename'),
            readonly=True, store={
                'banking.export.ch.dd': (
                    lambda self, cr, uid, ids, context: ids, ['type'], 10)}),
        'state': fields.selection([
                ('draft', _('Draft')),
                ('sent', _('Sent')),
        ], 'State', readonly=True),
        'type': fields.char(_('Type'), size=128, readonly=True),
    }

    _defaults = {
        'state': 'draft',
    }
