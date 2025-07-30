# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _ebill_tax_amount(self, tax):
        """Helper to compute tax amount for a given tax on invoice line.

        :param tax: The tax to compute.
        :return: Computed tax amount.
        """
        if not tax:
            return 0.0

        # Compute the tax amount
        price_unit = self.price_unit
        quantity = self.quantity
        currency = self.move_id.currency_id

        # Adjust price for discount
        discount = self.discount or 0.0
        price = price_unit * (1 - discount / 100)

        # Compute the tax amount using the tax's compute_all method
        res = tax.compute_all(
            price_unit=price,
            currency=currency,
            quantity=quantity,
            product=self.product_id,
            partner=self.move_id.partner_id,
        )
        return res["taxes"][0]["amount"]
