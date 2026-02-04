# Copyright 2024 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase


class TestAccountPaymentLine(TransactionCase):
    def test_communication_type_qrr_selection(self):
        """Test that QRR is available in communication_type selection"""
        # Get the field definition
        field = self.env["account.payment.line"]._fields.get("communication_type")

        # Check that the field exists
        self.assertIsNotNone(field)

        # Check that 'qrr' is in the selection
        selection_values = [item[0] for item in field.selection]
        self.assertIn("qrr", selection_values)
