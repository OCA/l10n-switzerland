import base64
import re

from lxml import etree

from odoo.addons.account_payment_return_import_iso20022.wizard.pain_parser import (
    PainParser,
)


class PainCHParser(PainParser):
    _name = "account.pain002.parser"
    _description = "Parse pain002 CH"

    @staticmethod
    def validate_status(file):
        """Validate the status of the pain 002"""
        root, ns = PainCHParser.parse_xml(base64.b64decode(file))
        STATUS_XML_NODE = "./ns:CstmrPmtStsRpt/ns:OrgnlGrpInfAndSts/ns:GrpSts"
        found_node = root.xpath(STATUS_XML_NODE, namespaces={"ns": ns})
        if found_node:
            return_status = found_node[0].text
            if return_status in ["ACTC", "ACCP"]:
                return True
            elif return_status == "PART":
                return True
            elif return_status == "RJCT":
                info_status = root.xpath(
                    "./ns:CstmrPmtStsRpt/ns:OrgnlGrpInfAndSts/ns:StsRsnInf/ns:AddtlInf",
                    namespaces={"ns": ns},
                )
                raise ValueError(f"File rejected !\nReason: {info_status[0].text}")
            else:
                raise ValueError("Status not known by Pain Parser CH")
        else:
            raise ValueError("Status Node not found")

    def parse_transaction(self, ns, node, transaction):
        """Parse transaction (entry) node."""
        super().parse_transaction(ns, node, transaction)
        self.add_value_from_node(ns, node, "./ns:TxSts", transaction, "concept")
        return transaction

    def check_version(self, ns, root):
        """Validate validity of pain 002 CH Report file."""
        # Check wether it is SEPA Direct Debit Unpaid Report at all:
        re_pain = re.compile(r"(^http://www.six-interbank-clearing.com/de/pain.)")
        if not re_pain.search(ns):
            raise ValueError("no pain: " + ns)
        # Check wether version 002.001.03.ch.02:
        re_pain_version = re.compile(
            r"(^urn:iso:std:iso:20022:tech:xsd:pain.002.001.03"
            r"|pain.002.001.03.ch.02)"
        )
        if not re_pain_version.search(ns):
            raise ValueError("no PAIN.002.001.03.ch.02: " + ns)
        # Check GrpHdr element:
        root_0_0 = root[0][0].tag[len(ns) + 2 :]  # strip namespace
        if root_0_0 != "GrpHdr":
            raise ValueError("expected GrpHdr, got: " + root_0_0)

    @staticmethod
    def parse_xml(payment_return):
        try:
            root = etree.fromstring(
                payment_return, parser=etree.XMLParser(recover=True)
            )
        except etree.XMLSyntaxError:
            # ABNAmro is known to mix up encodings
            root = etree.fromstring(
                payment_return.decode("iso-8859-15").encode("utf-8")
            )
        if root is None:
            raise ValueError("Not a valid xml file, or not an xml file at all.")
        return root, root.tag[1 : root.tag.index("}")]

    def parse(self, payment_return):
        """Parse a pain.002.001.03 file."""
        root, ns = self.parse_xml(payment_return)
        self.check_version(ns, root)
        payment_returns = []
        for node in root:
            payment_return = super().parse_payment_return(ns, node)

            if not payment_return["transactions"]:
                self.add_value_from_node(
                    ns,
                    node,
                    "./ns:OrgnlGrpInfAndSts/ns:StsRsnInf/ns:Rsn/ns:Cd",
                    payment_return,
                    "error_code",
                )
                self.add_value_from_node(
                    ns,
                    node,
                    "./ns:OrgnlGrpInfAndSts/ns:StsRsnInf/ns:AddtlInf",
                    payment_return,
                    "error",
                )

            self.add_value_from_node(
                ns,
                node,
                "./ns:OrgnlGrpInfAndSts/ns:OrgnlMsgId",
                payment_return,
                "order_name",
            )
            payment_returns.append(payment_return)
        return payment_returns
