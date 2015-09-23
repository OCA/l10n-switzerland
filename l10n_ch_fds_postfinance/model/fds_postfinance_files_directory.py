# -*- coding: utf-8 -*-
##############################################################################
#
#    Swiss Postfinance File Delivery Services module for Odoo
#    Copyright (C) 2014 Compassion CH
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


class fds_postfinance_files_directory(models.Model):
    ''' Keep directory name of each FDS folder in the database
    '''
    _name = 'fds.postfinance.files.directory'

    name = fields.Char(
        string='Directory name',
        readonly=True,
        help='name of the directory'
    )
    fds_account_id = fields.Many2one(
        comodel_name='fds.postfinance.account',
        string='FDS account id',
        ondelete='restrict',
        readonly=True,
        help='directory related with this FDS accout'
    )
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        help='choose one default journal (need to import to bank statment)'
    )
    allow_download_file = fields.Boolean(
        string='Allow download file?',
        default=False,
        help='check it to allow download files from this FDS directory to DB'
    )
    allow_upload_file = fields.Boolean(
        string='Allow upload file?',
        default=False,
        help='check it to allow upload files from BD to this FDS directory'
    )
    still_on_server = fields.Boolean(
        string='Directory still on server?',
        default=True,
        readonly=True,
        help='[info] if the directory still exist on the FDS sftp'
    )
