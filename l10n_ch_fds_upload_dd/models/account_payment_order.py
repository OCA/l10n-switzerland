# -*- coding: utf-8 -*-
##############################################################################
#
#    Swiss Postfinance File Delivery Services module for Odoo
#    Copyright (C) 2017 Compassion CH
#    @author: Emanuel Cino
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

from openerp import api, models


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    @api.multi
    def open2generated(self):
        """
        Replace action to propose upload DD file to FDS.
        :return: window action
        """
        action = super(AccountPaymentOrder, self).open2generated()
        if self.payment_method_id.code == 'postfinance.dd':
            upload_obj = self.env['payment.order.upload.dd.wizard']
            attachment_id = action['res_id']
            upload_wizard = upload_obj.create({
                'attachment_id': attachment_id,
                'payment_order_id': self.id,
            })
            del action['view_id']
            action.update({
                'res_model': upload_obj._name,
                'res_id': upload_wizard.id,
                'flags': {'initial_mode': 'edit'},
            })
        return action
