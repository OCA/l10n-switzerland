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


class FdsDdUploadHistory(models.Model):
    ''' History of direct debit uploads to FDS
    '''
    _name = 'fds.dd.upload.history'

    fds_account_id = fields.Many2one(
        comodel_name='fds.postfinance.account',
        string='FDS account',
        ondelete='restrict',
        readonly=True,
    )
    banking_export_id = fields.Many2one(
        comodel_name='banking.export.ch.dd',
        string='Direct debit export',
        ondelete='restrict',
        readonly=True,
    )
    filename = fields.Char(
        readonly=True,
        help='Remote name of the uploaded file'
    )
    directory_id = fields.Many2one(
        comodel_name='fds.postfinance.directory',
        string='Directory',
        ondelete='restrict',
        readonly=True,
        help='Remote directory where the file was uploaded'
    )
    state = fields.Selection(
        selection=[('not_uploaded', 'Not Uploaded'),
                   ('uploaded', 'Uploaded')],
        readonly=True,
        default='not_uploaded',
        help='Upload state of the file'
    )
