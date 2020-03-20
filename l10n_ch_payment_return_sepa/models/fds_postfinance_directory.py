# © 2015 Compassion CH (Nicolas Tran)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class FdsPostfinanceDirectory(models.Model):
    """ Keep directory name of each FDS folder in the database
    """
    _inherit = 'fds.postfinance.directory'

    file_type = fields.Selection(selection_add=[
        ('pain.002.001.03.ch.02',
         'pain.002.001.03.ch.02 (payment return)')
    ])
