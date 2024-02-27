# Copyright 2023 Compassion CH (https://www.compassion.ch)
# @author: Simon Gonzalez <simon.gonzalez@bluewin.ch>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64

from odoo.addons.component.core import Component

from ..wizard.pain_parser_ch import PainParserCH


class EDIExchangeProcessPaymentReturn(Component):
    """ACK for payment order pain002.01.03.CH"""

    _name = "edi.input.payment.ch.process"
    _inherit = "edi.component.input.mixin"
    _backend_type = "sftp_pay_ord_ack"
    _usage = "input.process"

    def process(self):
        origin_output = self.exchange_record.parent_id
        payment_order = self.env[origin_output.model].browse(
            self.exchange_record.parent_id.res_id
        )
        try:
            PainParserCH().validate_initial_return(
                base64.b64decode(self.exchange_record.exchange_file)
            )
        except Exception as e:
            payment_order.action_cancel()
            raise e
        payment_order.generated2uploaded()
