# © 2020 Quentin Gigon <gigon.quentin@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, api
from odoo.tools import safe_eval


class AccountInvoicePaymentLineMulti(models.TransientModel):
    _inherit = 'account.invoice.payment.line.multi'

    @api.multi
    def run(self):
        action = super().run()

        domain = safe_eval(action['domain'])
        orders = self.env[action['res_model']].browse(domain[0][2]).exists()
        for order in orders:
            if order.payment_type == "inbound":
                if order.company_partner_bank_id.bank_id.clearing == "9000":
                    # Force correct values for Postfinance
                    order.payment_line_ids.write({
                        "local_instrument": "DDCOR1",
                        "communication_type": "normal"
                    })
                else:
                    # No other types than LSV+ in Switzerland
                    order.payment_line_ids.write({
                        "local_instrument": "LSV+",
                    })
        return action
