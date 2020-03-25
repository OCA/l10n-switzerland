# © 2015 Compassion CH (Nicolas Tran)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models
from odoo.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)


class FdsFilesImportFromFDSWizard(models.TransientModel):
    _inherit = 'fds.files.import.from.fds.wizard'

    def process_files(self, file):
        """ function that import the files to payment return
            :param file: file of model fds_postfinance_file
            :returns None:
        """
        try:
            file.import_to_bank_statements()
            if file.state == 'error':
                self.msg_import_file_fail += file['filename'] + '\n'
            else:
                self.msg_file_imported += file['filename'] + '\n'
        except UserError:
            return super().process_files(file)
