from odoo import models, fields


class FdsPostfinanceDirectory(models.Model):
    """ Keep directory name of each FDS folder in the database
    """
    _inherit = 'fds.postfinance.directory'

    file_type = fields.Selection(selection_add=[
        ('camt.054', 'CAMT 054 Postfinance Statement')
    ])
