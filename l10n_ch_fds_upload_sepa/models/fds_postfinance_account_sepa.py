# -*- coding: utf-8 -*-
# © 2015 Compassion CH (Nicolas Tran)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdsPostfinanceAccountSepa(models.Model):
    ''' Add SEPA upload history to the model fds.postfinance.account
    '''
    _inherit = 'fds.postfinance.account'

    sepa_upload_ids = fields.One2many(
        comodel_name='fds.sepa.upload.history',
        inverse_name='fds_account_id',
        readonly=True,
    )
