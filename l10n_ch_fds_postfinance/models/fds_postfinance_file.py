# © 2015 Compassion CH (Nicolas Tran)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class FdsPostfinanceFile(models.Model):
    """ Model of the information and files downloaded on FDS PostFinance
        (Keep files in the database)
    """
    _name = 'fds.postfinance.file'

    fds_account_id = fields.Many2one(
        comodel_name='fds.postfinance.account',
        string='FDS account',
        ondelete='restrict',
        readonly=True,
        help='related FDS account'
    )
    data = fields.Binary(
        readonly=True,
        help='the downloaded file data'
    )
    filename = fields.Char(
        readonly=True
    )
    directory_id = fields.Many2one(
        'fds.postfinance.directory',
        string='Directory',
        ondelete='restrict',
        readonly=True,
    )
    file_type = fields.Selection(
        [],
        help="Install sub-modules to support various file types provided by "
             "Postfinance."
    )
    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('done', 'Done'),
                   ('error', 'Error'),
                   ('cancel', 'Cancelled')],
        readonly=True,
        default='draft',
        help='state of file'
    )
    error_message = fields.Text()

    ##################################
    #         Button action          #
    ##################################
    @api.multi
    def change2error_button(self):
        """ change the state of the file to error because the file is corrupt.
            Called by pressing 'corrupt file?' button.

            :return None:
        """
        valid_files = self.filtered(lambda f: f.state == 'draft')
        valid_files.write({'state': 'error'})

    @api.multi
    def change2draft_button(self):
        """ undo the file is corrupt to state draft.
            Called by pressing 'cancel corrupt file' button.

            :return None:
        """
        self.write({'state': 'draft'})

    @api.multi
    def change2cancel_button(self):
        """ Put file in cancel state.
            Called by pressing 'cancel' button.

            :return None:
        """
        valid_files = self.filtered(lambda f: f.state in ('error', 'draft'))
        valid_files.write({'state': 'cancel'})
