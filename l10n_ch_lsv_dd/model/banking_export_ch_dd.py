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
from openerp import models, fields, api, _
from openerp.addons.decimal_precision import decimal_precision as dp

import logging
logger = logging.getLogger(__name__)


class banking_export_ch_dd(models.Model):

    ''' Swiss Direct Debit export containing the file created
        by the appropriate wizard
    '''
    _name = 'banking.export.ch.dd'
    _rec_name = 'filename'

    def _generate_filename(self):
        self.ensure_one()
        ref = self.env['ir.sequence'].next_by_code('l10n.banking.'
                                                   'export.filename')
        username = self.env.user.name
        initials = ''.join([subname[0] for subname in username.split()])
        if self.type == 'LSV':
            res = 'lsv_%s_%s.lsv' % (ref, initials)
        else:
            res = 'dd_%s_%s.dd' % (ref, initials)
        self.filename = res
        return True

    @api.model
    def create(self, vals):
        res = super(banking_export_ch_dd, self).create(vals)
        res._generate_filename()
        return res

    payment_order_ids = fields.Many2many(
        'payment.order',
        'account_payment_order_ch_dd_rel',
        'banking_export_ch_dd_id',
        'account_order_id',
        _('Payment Orders'),
        readonly=True
    )
    nb_transactions = fields.Integer(
        _('Number of Transactions'),
        readonly=True
    )
    total_amount = fields.Float(
        _('Total Amount'),
        readonly=True,
        digits_compute=dp.get_precision('Account')
    )
    create_date = fields.Datetime(
        _('Generation Date'),
        readonly=True
    )
    file = fields.Binary(
        _('Generated file'),
        readonly=True
    )
    filename = fields.Char(
        string=_('Filename'),
        size=256,
        readonly=True,
    )
    state = fields.Selection(
        [('draft', _('Draft')), ('sent', _('Sent'))],
        'State',
        readonly=True,
        default='draft'
    )
    type = fields.Char(
        _('Type'),
        size=128,
        readonly=True
    )
