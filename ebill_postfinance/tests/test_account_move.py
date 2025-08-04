# Copyright 2025 Camptocamp SA (https://www.camptocamp.com).
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import CommonCase


@tagged("post_install", "-at_install")
class TestAccountMove(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.transmit_method_pf = cls.env.ref(
            "ebill_postfinance.postfinance_transmit_method"
        )
        cls.pf_partner_bank = cls.env["res.partner.bank"].create(
            {
                "bank_id": cls.bank.id,
                "acc_number": "CH04 8914 4618 6435 6132 1",
                "acc_holder_name": "AccountHolderPF",
                "partner_id": cls.company.partner_id.id,
            }
        )
        cls.contract.postfinance_service_id.partner_bank_id = cls.pf_partner_bank
        cls.transmit_method_not_pf = cls.env["transmit.method"].create(
            {
                "name": "TESTNOTPF",
                "code": "testnotpf",
                "customer_ok": True,
            }
        )

    @mute_logger("odoo.addons.base_ebill_payment_contract.models.res_partner")
    def test_compute_bank_partner_no_active_contract(self):
        self.assertFalse(
            self.invoice.partner_id.get_active_contract(self.transmit_method_pf)
        )
        self.assertFalse(self.invoice.transmit_method_id)
        self.invoice.transmit_method_id = self.transmit_method_not_pf
        self.assertNotEqual(self.invoice.partner_bank_id, self.pf_partner_bank)
        self.invoice.transmit_method_id = self.transmit_method_pf
        self.assertNotEqual(self.invoice.partner_bank_id, self.pf_partner_bank)

    @mute_logger("odoo.addons.base_ebill_payment_contract.models.res_partner")
    def test_compute_bank_partner_active_contract(self):
        self.contract.transmit_method_id = self.transmit_method_pf
        self.assertTrue(
            self.invoice.partner_id.get_active_contract(self.transmit_method_pf)
        )
        self.assertFalse(self.invoice.transmit_method_id)
        self.invoice.transmit_method_id = self.transmit_method_not_pf
        self.assertNotEqual(self.invoice.partner_bank_id, self.pf_partner_bank)
        self.invoice.transmit_method_id = self.transmit_method_pf
        self.assertEqual(self.invoice.partner_bank_id, self.pf_partner_bank)
