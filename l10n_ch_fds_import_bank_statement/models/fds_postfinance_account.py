# # © 2015 Compassion CH (Nicolas Tran)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class FdsPostfinanceAccount(models.Model):
    """" the FDS PostFinance configuration that allow to connect to the
        PostFinance server
    """
    _inherit = 'fds.postfinance.account'

    camt_file_ids = fields.One2many(
        comodel_name='fds.postfinance.file',
        inverse_name='fds_account_id',
        string='CAMT Postfinance files',
        readonly=True,
        help='downloaded camt 054 files from sftp',
        compute="_compute_filter_camt"
    )

    @api.multi
    def _compute_filter_camt(self):
        self.camt_file_ids = self.fds_file_ids.filtered(
            lambda j: j.file_type == 'camt.054')
