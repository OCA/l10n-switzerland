# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class EbillPaymentContract(models.Model):
    _inherit = "ebill.payment.contract"

    postfinance_billerid = fields.Char(
        string="Contract ID", size=20, help="The PayerID of the customer"
    )
    is_postfinance_contract = fields.Boolean(
        compute="_compute_is_postfinance_contract", store=False
    )
    postfinance_service_id = fields.Many2one(
        comodel_name="ebill.postfinance.service",
        string="Service",
        ondelete="restrict",
    )
    is_postfinance_method_on_partner = fields.Boolean(
        compute="_compute_is_postfinance_method_on_partner"
    )
    payment_type = fields.Selection(
        selection=[("qr", "QR")],
        string="Payment method",
        default="qr",
        help="Payment type to use for the invoices sent,"
        " PDF will be generated and attached accordingly.",
    )

    @api.depends("transmit_method_id")
    def _compute_is_postfinance_contract(self):
        transmit_method = self.env.ref("ebill_postfinance.postfinance_transmit_method")
        for record in self:
            record.is_postfinance_contract = (
                record.transmit_method_id == transmit_method
            )

    @api.depends("transmit_method_id", "partner_id", "postfinance_service_id")
    def _compute_is_postfinance_method_on_partner(self):
        transmit_method = self.env.ref("ebill_postfinance.postfinance_transmit_method")
        for record in self:
            record.is_postfinance_method_on_partner = (
                record.partner_id.customer_invoice_transmit_method_id == transmit_method
            )

    def set_postfinance_method_on_partner(self):
        transmit_method = self.env.ref("ebill_postfinance.postfinance_transmit_method")
        for record in self:
            if record.partner_id:
                record.partner_id.customer_invoice_transmit_method_id = transmit_method

    @api.constrains("transmit_method_id", "postfinance_billerid")
    def _check_postfinance_biller_id(self):
        for contract in self:
            if not contract.is_postfinance_contract:
                continue
            if not contract.postfinance_billerid:
                raise ValidationError(
                    _(
                        "The Postfinacnce Account ID is required for a "
                        "Postfinance contract."
                    )
                )

    @api.constrains("transmit_method_id", "postfinance_service_id")
    def _check_postfinance_service_id(self):
        for contract in self:
            if contract.is_postfinance_contract and not contract.postfinance_service_id:
                raise ValidationError(
                    self.env._(
                        "A Postfinance service is required for a Postfinance contract."
                    )
                )
