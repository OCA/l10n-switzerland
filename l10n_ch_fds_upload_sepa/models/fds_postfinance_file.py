# -*- coding: utf-8 -*-
# © 2015 Compassion CH (Nicolas Tran)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class FdsPostfinanceFile(models.Model):
    ''' Model of the information and files downloaded on FDS PostFinance
        (Keep files in the database)
    '''
    _inherit = 'fds.postfinance.file'

    payment_order = fields.Many2one(
        'account.payment.order',
        string='Payment order',
        ondelete='restrict',
        readonly=True,
    )
