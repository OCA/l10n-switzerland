# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import os

from odoo.tests.common import SingleTransactionCase

from ..components.api import PayNetDWS
from .common import recorder


class TestEbillPaynet(SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.paynet = cls.env["paynet.service"].create(
            {
                "use_test_service": True,
                "client_pid": os.getenv("PAYNET_ID", "123456789"),
                "service_type": "b2b",
            }
        )
        cls.dws = PayNetDWS(cls.paynet.url, True)
        cls.customer = cls.env["res.partner"].create(
            {"name": "Customer One", "customer_rank": 1}
        )
        cls.contract = cls.env["ebill.payment.contract"].create(
            {
                "partner_id": cls.customer.id,
                "paynet_account_number": "123123123",
                "state": "open",
                "paynet_service_id": cls.paynet.id,
            }
        )
        cls.account = cls.env["account.account"].search(
            [
                (
                    "user_type_id",
                    "=",
                    cls.env.ref("account.data_account_type_revenue").id,
                )
            ],
            limit=1,
        )
        cls.at_receivable = cls.env["account.account.type"].create(
            {
                "name": "Test receivable account",
                "type": "receivable",
                "internal_group": "asset",
            }
        )
        cls.a_receivable = cls.env["account.account"].create(
            {
                "name": "Test receivable account",
                "code": "TEST_RA",
                "user_type_id": cls.at_receivable.id,
                "reconcile": True,
            }
        )
        cls.product = cls.env["product.template"].create(
            {"name": "Product One", "list_price": 100.00}
        )
        cls.invoice_1 = cls.env["account.move"].create(
            {
                "partner_id": cls.customer.id,
                # 'account_id': cls.account.id,
                "type": "out_invoice",
                "transmit_method_id": cls.env.ref(
                    "ebill_paynet.paynet_transmit_method"
                ).id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": cls.account.id,
                            "product_id": cls.product.product_variant_ids[:1].id,
                            "name": "Product 1",
                            "quantity": 1.0,
                            "price_unit": 100.00,
                        },
                    )
                ],
            }
        )

    @recorder.use_cassette
    def test_ping_service(self):
        """Check the ping service testing purpose only."""
        self.dws.service.ping()

    @recorder.use_cassette
    def test_takeShipment(self):
        """Check sending a file to the service."""
        ch = self.env.ref("base.ch")
        attachment = self.env["ir.attachment"].search(
            [["res_model", "=", "res.country"], ["res_id", "=", ch.id]]
        )
        attachment = self.env.ref("mail.msg_discus4_attach1")
        shipment_id = self.paynet.take_shipment(attachment[0].datas.decode())
        self.assertTrue(shipment_id.startswith("SC"))
        # The shipment is not found on the server ?
        # self.paynet.get_shipment_content(shipment_id)

    @recorder.use_cassette
    def test_getShipmentList(self):
        """Check getting a list of file on the service."""
        res = self.paynet.get_shipment_list()
        self.assertTrue("entriesFound" in res)

    @recorder.use_cassette
    def test_getShipmentContent(self):
        """Check getting the content of a file.

        This one is CONTRL NOK
        """
        message = self.invoice_1.create_paynet_message()
        message.ic_ref = "SA000000000003"
        res = self.paynet.get_shipment_content("SC-00000000000020357011")
        self.paynet.handle_received_shipment(res, "SC-00000000000020357011")
        self.assertEqual(message.state, "error")
