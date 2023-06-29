# Copyright 2023 Compassion CH - Simon Gonzalez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import re

from lxml import etree

from odoo.addons.account_payment_return_import_iso20022.wizard.pain_parser import (
    PainParser,
)

_logger = logging.getLogger(__name__)

ACCEPTANCE_STATUS = ["ACCP", "ACWC", "ACTC"]


class AcceptedEmptyByBankException(ValueError):
    pass


class PainParserCH(PainParser):
    """Parser for SEPA Direct Debit Unpaid Report import files."""

    def _get_root_ns(self, data):
        try:
            root = etree.fromstring(data, parser=etree.XMLParser(recover=True))
        except etree.XMLSyntaxError:
            # ABNAmro is known to mix up encodings
            root = etree.fromstring(data.decode("iso-8859-15").encode("utf-8"))
        if root is None:
            raise ValueError("Not a valid xml file, or not an xml file at all.")
        ns = root.tag[1 : root.tag.index("}")]
        self.check_version(ns, root)
        return root, ns

    def get_origin_msg(self, file):
        root, ns = self._get_root_ns(file)
        ORIGIN_MSG_XML_NODE = (
            "./ns:CstmrPmtStsRpt/ns:OrgnlGrpInfAndSts/ns:OrgnlMsgId",
        )
        found_node = root.xpath(ORIGIN_MSG_XML_NODE, namespaces={"ns": ns})
        return found_node[0].text

    def check_version(self, ns, root):
        """Validate validity of SEPA Direct Debit Unpaid Report file."""
        # Check wether it is SEPA Direct Debit Unpaid Report at all:
        re_pain = re.compile(r"^http://www.six-interbank-clearing.com/.*/pain")
        if not re_pain.search(ns):
            raise ValueError("no pain: " + ns)
        # Check wether version 002.001.03.ch:
        re_pain_version = re.compile(r"|pain.002.001.03.ch.02.xsd")
        if not re_pain_version.search(ns):
            raise ValueError("no PAIN.002.001.03: " + ns)
        # Check GrpHdr element:
        root_0_0 = root[0][0].tag[len(ns) + 2 :]  # strip namespace
        if root_0_0 != "GrpHdr":
            raise ValueError("expected GrpHdr, got: " + root_0_0)

    def validate_grp_status(self, ns, root):
        """Validate the status of the pain 002"""
        STATUS_XML_NODE = "./ns:CstmrPmtStsRpt/ns:OrgnlGrpInfAndSts/ns:GrpSts"
        found_node = root.xpath(STATUS_XML_NODE, namespaces={"ns": ns})
        if found_node:
            return_status = found_node[0].text
            _logger.info(f"File has this status {return_status}")
            if return_status in ACCEPTANCE_STATUS:
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

    def validate_initial_return(self, data):
        root, ns = self._get_root_ns(data)
        self.validate_grp_status(ns, root)
        return root, ns

    def parse(self, data):
        """Parse a pain.002.001.03 file."""
        root, ns = self.validate_initial_return(data)
        payment_returns = []
        for node in root:
            payment_return = super().parse_payment_return(ns, node)
            if payment_return["transactions"]:
                if not payment_return.get("account_number"):
                    payment_return["account_number"] = False
                payment_returns.append(payment_return)
        return payment_returns
