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


class fds_postfinance_account_dd(models.Model):
    ''' Add default upload directory to the model fds.postfinance.account
    '''
    _inherit = 'fds.postfinance.account'

    upload_dd_directory = fields.Many2one(
        comodel_name='fds.postfinance.files.directory',
        string='default upload directory',
        help='select one upload default directory.' +
             ' if none, allow upload file first'
    )
    historical_dd = fields.One2many(
        comodel_name='fds.postfinance.historical.dd',
        inverse_name='fds_account_id',
        string='historical upload dd',
        readonly=True,
        help='historical upload dd'
    )
