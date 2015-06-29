# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Vincent Renaville
#    Copyright 2015 Camptocamp SA
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
from openerp import models, api


class payment_line(models.Model):
    _inherit = 'payment.line'

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        """In case of BVR
        we will search the transaction ref instead of ref for
        communication field"""
        account_move_line_obj = self.env['account.move.line']
        move_line = account_move_line_obj.browse(vals['move_line_id'])
        if move_line.transaction_ref:
            vals['communication'] = move_line.transaction_ref
        return super(payment_line, self).create(vals)
