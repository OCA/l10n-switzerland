# Copyright 2021-2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from ...ebill_postfinance.tests.common import CommonCase


class TestEbillPosfinanceCustomerFreeRef(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.invoice.name = "INV_TEST_01"
        cls.sale.customer_order_number = "888"
        cls.sale.customer_order_free_ref = "FREE"

    def test_one(self):
        self.assertEqual(self.sale.postfinance_ebill_client_order_ref, "888")
        self.assertEqual(
            self.invoice.get_postfinance_other_reference(),
            [{"type": "CR", "no": "FREE"}],
        )
