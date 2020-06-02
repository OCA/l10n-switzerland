# © 2016 Akretion (<https://www.akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class AccountInvoicePaymentLineMulti(models.TransientModel):
    _inherit = 'account.invoice.payment.line.multi'

    @api.multi
    def run(self):
        action = super().run()

        order = self.env[action['res_model']].browse(action['res_id'])
        if order.payment_type == "inbound":
            local_instrument = ""
            if order.company_partner_bank_id.acc_type == "iban":
                local_instrument = "LSV+"
            elif order.company_partner_bank_id.acc_type == "postal":
                local_instrument = "DDCOR1"
            order.payment_line_ids.write({
                "local_instrument": local_instrument
            })
        return action
