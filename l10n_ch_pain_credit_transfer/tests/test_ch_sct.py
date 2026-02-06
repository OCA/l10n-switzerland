# (c) 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from datetime import date

from lxml import etree

from odoo.tests import tagged
from odoo.tools import float_compare

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

# test business case and data based on chapter 5 of official documentation
# https://www.six-group.com/dam/download/banking-services/standardization/sps/ig-credit-transfer-sps-2025-en.pdf # noqa: B950
ch_iban = "CH72 8000 5000 0888 7776 6"


@tagged("post_install", "-at_install")
class TestSCTCH(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref="l10n_ch.l10nch_chart_template"):
        super().setUpClass(chart_template_ref)
        Journal = cls.env["account.journal"]
        PaymentMode = cls.env["account.payment.mode"]
        Account = cls.env["account.account"]

        cls.payment_order_model = cls.env["account.payment.order"]
        cls.payment_line_model = cls.env["account.payment.line"]
        cls.partner_model = cls.env["res.partner"]
        cls.bank_model = cls.env["res.bank"]
        cls.partner_bank_model = cls.env["res.partner.bank"]
        cls.attachment_model = cls.env["ir.attachment"]
        cls.account_move_model = cls.env["account.move"]

        cls.account_expense = Account.search(
            [
                (
                    "account_type",
                    "=",
                    "expense",
                )
            ],
            limit=1,
        )
        cls.account_payable = Account.search(
            [
                (
                    "account_type",
                    "=",
                    "liability_payable",
                )
            ],
            limit=1,
        )
        # Create a swiss bank
        ch_bank1 = cls.bank_model.create(
            {
                "name": "Raiffeisen",
                "bic": "RAIFCH22005",
            }
        )
        # create a ch bank account for my company
        cls.cp_partner_bank = cls.partner_bank_model.create(
            {
                "acc_number": ch_iban,
                "partner_id": cls.env.user.company_id.partner_id.id,
            }
        )
        # create journal
        cls.bank_journal = Journal.create(
            {
                "name": "Company Bank journal",
                "type": "bank",
                "code": "BNKFB",
                "bank_account_id": cls.cp_partner_bank.id,
                "bank_id": ch_bank1.id,
            }
        )
        # create a payment mode
        pay_method_id = cls.env.ref(
            "account_banking_sepa_credit_transfer.sepa_credit_transfer"
        ).id
        cls.payment_mode = PaymentMode.create(
            {
                "name": "CH credit transfer",
                "bank_account_link": "fixed",
                "fixed_journal_id": cls.bank_journal.id,
                "payment_method_id": pay_method_id,
            }
        )
        cls.payment_mode.payment_method_id.pain_version = "pain.001.001.09.ch.03"
        cls.chf_currency = cls.env.ref("base.CHF")
        cls.eur_currency = cls.env.ref("base.EUR")

        # Create a swiss customer with QRR bank
        cls.swiss_partner_1 = cls.partner_model.create(
            {
                "name": "Robert Scheider Ltd",
                "street": "Rue du Lac 1268",
                "zip": "2501",
                "city": "Biel",
                "country_id": cls.env.ref("base.ch").id,
            }
        )
        ch_bank_be = cls.bank_model.create(
            {
                "name": "BEKB | BCBE",
                "street": "Bundesplatz 8",
                "zip": "3001",
                "city": "Bern",
                "country": cls.env.ref("base.ch").id,
            }
        )
        cls.swiss_partner_1_bank = cls.partner_bank_model.create(
            {
                "acc_number": "CH44 3199 9123 0008 8901 2",
                "partner_id": cls.swiss_partner_1.id,
                "bank_id": ch_bank_be.id,
            }
        )

        # Create a swiss customer with normal bank
        cls.swiss_partner_2 = cls.partner_model.create(
            {
                "name": "Peter Haller",
                "street": "Rosenauweg 4",
                "zip": "8036",
                "city": "Zürich",
                "country_id": cls.env.ref("base.ch").id,
            }
        )
        ch_bank_zh = cls.bank_model.create(
            {
                "name": "Zürcher Kantonalbank",
                "street": "Bahnhofstrasse 9",
                "zip": "8001",
                "city": "Zürich",
                "country": cls.env.ref("base.ch").id,
            }
        )
        cls.swiss_partner_2_bank = cls.partner_bank_model.create(
            {
                "acc_number": "CH48 2196 6000 0096 1338 8",
                "partner_id": cls.swiss_partner_2.id,
                "bank_id": ch_bank_zh.id,
            }
        )

    def test_ch_payment_qrr_normal(self):
        # QRR invoice
        invoice1 = self.create_invoice(
            self.swiss_partner_1.id,
            self.swiss_partner_1_bank.id,
            self.chf_currency,
            3949.75,
            "21 00000 00003 13947 14300 09017",
        )
        # normal invoice
        invoice2 = self.create_invoice(
            self.swiss_partner_2.id,
            self.swiss_partner_2_bank.id,
            self.eur_currency,
            199.95,
            "normal ref",
        )
        for inv in [invoice1, invoice2]:
            action = inv.create_account_payment_line()
        self.assertEqual(action["res_model"], "account.payment.order")
        self.payment_order = self.payment_order_model.browse(action["res_id"])
        self.assertEqual(self.payment_order.payment_type, "outbound")
        self.assertEqual(self.payment_order.payment_mode_id, self.payment_mode)
        self.assertEqual(self.payment_order.journal_id, self.bank_journal)
        pay_lines = self.payment_line_model.search(
            [
                ("order_id", "=", self.payment_order.id),
            ]
        )
        self.assertEqual(len(pay_lines), 2)
        qrr_pay_line = pay_lines.search(
            [
                ("partner_id", "=", self.swiss_partner_1.id),
            ],
            limit=1,
        )
        accpre = self.env["decimal.precision"].precision_get("Account")
        self.assertEqual(qrr_pay_line.currency_id, self.chf_currency)
        self.assertEqual(qrr_pay_line.partner_bank_id, invoice1.partner_bank_id)
        self.assertEqual(
            float_compare(
                qrr_pay_line.amount_currency, 3949.75, precision_digits=accpre
            ),
            0,
        )
        self.assertEqual(qrr_pay_line.communication_type, "qrr")
        self.assertEqual(qrr_pay_line.communication, "210000000003139471430009017")
        normal_pay_line = pay_lines.search(
            [
                ("partner_id", "=", self.swiss_partner_2.id),
            ],
            limit=1,
        )
        self.assertEqual(normal_pay_line.communication_type, "normal")
        self.assertEqual(normal_pay_line.communication, "normal ref")
        self.payment_order.draft2open()
        self.assertEqual(self.payment_order.state, "open")
        self.assertEqual(self.payment_order.sepa, False)
        action = self.payment_order.open2generated()
        self.assertEqual(self.payment_order.state, "generated")
        self.assertEqual(action["res_model"], "ir.attachment")
        attachment = self.attachment_model.browse(action["res_id"])
        self.assertEqual(attachment.name[-4:], ".xml")
        xml_file = base64.b64decode(attachment.datas)
        xml_root = etree.fromstring(xml_file)
        namespaces = xml_root.nsmap
        namespaces["p"] = xml_root.nsmap[None]
        namespaces.pop(None)
        self.assertEqual(
            namespaces["p"],
            "urn:iso:std:iso:20022:tech:xsd:pain.001.001.09",
        )
        pay_method_xpath = xml_root.xpath("//p:PmtInf/p:PmtMtd", namespaces=namespaces)
        self.assertEqual(pay_method_xpath[0].text, "TRF")
        sepa_xpath = xml_root.xpath(
            "//p:PmtInf/p:PmtTpInf/p:SvcLvl/p:Cd", namespaces=namespaces
        )
        self.assertEqual(len(sepa_xpath), 0)

        debtor_acc_xpath = xml_root.xpath(
            "//p:PmtInf/p:DbtrAcct/p:Id/p:IBAN", namespaces=namespaces
        )
        self.assertEqual(
            debtor_acc_xpath[0].text,
            self.payment_order.company_partner_bank_id.sanitized_acc_number,
        )
        qrr_xpath = xml_root.xpath(
            "//p:PmtInf/p:CdtTrfTxInf/p:RmtInf/p:Strd/p:CdtrRefInf/p:Ref",
            namespaces=namespaces,
        )
        self.assertEqual(
            qrr_xpath[0].text,
            "210000000003139471430009017",
        )
        normal_xpath = xml_root.xpath(
            "//p:PmtInf/p:CdtTrfTxInf[2]/p:RmtInf/p:Ustrd", namespaces=namespaces
        )
        self.assertEqual(
            normal_xpath[0].text,
            "normal ref",
        )
        self.payment_order.generated2uploaded()
        self.assertEqual(self.payment_order.state, "uploaded")
        for inv in [invoice1, invoice2]:
            self.assertEqual(inv.state, "posted")
        return

    def create_invoice(
        self,
        partner_id,
        partner_bank_id,
        currency,
        price_unit,
        ref,
        inv_type="in_invoice",
    ):
        invoice = self.account_move_model.create(
            {
                "partner_id": partner_id,
                "ref": ref,
                "currency_id": currency.id,
                "move_type": inv_type,
                "name": "/",
                "payment_mode_id": self.payment_mode.id,
                "partner_bank_id": partner_bank_id,
                "invoice_date": date.today(),
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "price_unit": price_unit,
                            "quantity": 1,
                            "name": "Great service",
                            "account_id": self.account_expense.id,
                            "tax_ids": False,
                        },
                    )
                ],
            }
        )
        invoice.action_post()
        return invoice
