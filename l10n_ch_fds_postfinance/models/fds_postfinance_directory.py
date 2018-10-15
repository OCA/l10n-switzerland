# -*- coding: utf-8 -*-
##############################################################################
#
#    Swiss Postfinance File Delivery Services module for Odoo
#    Copyright (C) 2015 Compassion CH
#    @author: Nicolas Tran
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        help='default journal needed to import to bank statements'
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
        default='',
        help="Semicolon (;) separated patterns. If a filename matches one of "
        "the given patterns, the file won't be downloaded from the remote "
        "directory."
    )
