# © 2015 Compassion CH (Nicolas Tran)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models
from odoo.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)

try:
    import pysftp

    SFTP_OK = True
except ImportError:
    SFTP_OK = False
    _logger.error(
        'This module needs pysftp to connect to the FDS. '
        'Please install pysftp on your system. (sudo pip install pysftp)'
    )


class FdsFilesImportFromFDSWizard(models.TransientModel):
    _inherit = 'fds.files.import.from.fds.wizard'

    def process_files(self, file):
        """ function that import the files to payment return
            :param file: file of model fds_postfinance_file
            :returns None:
        """
        try:
            file.import_to_payment_return()
            error = file.filtered(lambda r: r.state == 'error')
            success = file - error
            self.msg_file_imported += '; '.join(success.mapped('filename'))
            self.msg_import_file_fail += '; '.join(error.mapped('filename'))
        except UserError:
            return super().process_files(file)
