# © 2015 Compassion CH (Nicolas Tran)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class FdsPostfinanceFile(models.Model):
    """ Model of the information and files downloaded on FDS PostFinance
        (Keep files in the database)
    """
    _inherit = 'fds.postfinance.file'

    file_type = fields.Selection(selection_add=[
        ('pain.002.001.03.ch.02',
         'pain.002.001.03.ch.02 (payment return)')
    ])
