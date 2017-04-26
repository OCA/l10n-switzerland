# -*- coding: utf-8 -*-
# © 2015 Compassion CH (Nicolas Tran)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdsPostfinanceDirectory(models.Model):
    ''' Keep directory name of each FDS folder in the database
    '''
    _name = 'fds.postfinance.directory'

    name = fields.Char(
        string='Directory name',
        readonly=True,
    )
    fds_account_id = fields.Many2one(
        comodel_name='fds.postfinance.account',
        string='FDS account',
        ondelete='restrict',
        readonly=True,
    )
    allow_download_file = fields.Boolean(
        string='Allow download file?',
        default=False,
        help='check it to allow download files from this FDS directory'
    )
    allow_upload_file = fields.Boolean(
        string='Allow upload file?',
        default=False,
        help='check it to allow upload files to this FDS directory'
    )
    still_on_server = fields.Boolean(
        string='Directory still on server?',
        default=True,
        readonly=True,
        help='[info] if the directory still exist on the FDS sftp'
    )
    excluded_files = fields.Char(
        default='camt052',
        help="Semicolon (;) separated patterns. If a filename matches one of "
        "the given patterns, the file won't be downloaded from the remote "
        "directory."
    )
