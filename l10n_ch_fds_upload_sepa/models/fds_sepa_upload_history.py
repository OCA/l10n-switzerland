# -*- coding: utf-8 -*-
# © 2015 Compassion CH (Nicolas Tran)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdsSepaUploadHistory(models.Model):
    ''' History of SEPA FDS uploads
    '''
    _name = 'fds.sepa.upload.history'

    fds_account_id = fields.Many2one(
        comodel_name='fds.postfinance.account',
        string='FDS account',
        ondelete='restrict',
        readonly=True,
    )
    payment_order_id = fields.Many2one(
        comodel_name='account.payment.order',
        string='Payment order',
        ondelete='restrict',
        readonly=True,
    )
    filename = fields.Char(
        readonly=True,
        help='Remote name of the uploaded file'
    )
    directory_id = fields.Many2one(
        comodel_name='fds.postfinance.directory',
        string='Directory',
        ondelete='restrict',
        readonly=True,
        help='Remote directory where the file was uploaded'
    )
    state = fields.Selection(
        selection=[('not_uploaded', 'Not Uploaded'),
                   ('uploaded', 'Uploaded')],
        readonly=True,
        default='not_uploaded',
        help='Upload state of the file'
    )
