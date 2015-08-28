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


class fds_postfinance_historical_dd(models.Model):
    ''' Add historical direct debit order to the model fds.postfinance.account
    '''
    _name = 'fds.postfinance.historical.dd'

    fds_account_id = fields.Many2one(
        comodel_name='fds.postfinance.account',
        string='FDS account id',
        ondelete='restrict',
        readonly=True,
        help='file related to FDS account id'
    )
    banking_export_id = fields.Many2one(
        comodel_name='banking.export.ch.dd',
        string='banking export id',
        ondelete='restrict',
        readonly=True,
        help='bankng export id'
    )
    filename = fields.Char(
        string='Filename',
        readonly=True,
        help='The name of the file'
    )
    directory_id = fields.Many2one(
        comodel_name='fds.postfinance.files.directory',
        string='Directory',
        ondelete='restrict',
        readonly=True,
        help='location directory of the file'
    )
    state = fields.Selection(
        selection=[('not_uploaded', 'Not Uploaded'),
                   ('uploaded', 'Uploaded')],
        readonly=True,
        default='not_uploaded',
        help='state of file'
    )
