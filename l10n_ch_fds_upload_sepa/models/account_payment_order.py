# -*- coding: utf-8 -*-
# © 2015 Compassion CH (Nicolas Tran)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    @api.multi
    def open2generated(self):
        """
        Replace action to propose upload SEPA file to FDS.
        :return: window action
        """
        action = super(AccountPaymentOrder, self).open2generated()
        if self.payment_method_id.code == 'sepa_credit_transfer':
            upload_obj = self.env['payment.order.upload.sepa.wizard']
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
