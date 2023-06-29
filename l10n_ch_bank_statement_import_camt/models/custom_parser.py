import re
import string

from odoo import _, models


class CustomParser(models.AbstractModel):
    _inherit = "account.statement.import.camt.parser"

    def parse_entry(self, ns, node):
        """Parse an Ntry node and yield transactions"""

        # Get some basic infos about the transaction in the XML.
        transaction = {
            "payment_ref": "/",
            "amount": 0,
            "narration": {},
            "transaction_type": {},
        }

        self.add_value_from_node(
            ns, node, "./ns:BkTxCd/ns:Prtry/ns:Cd", transaction, "transaction_type"
        )
        self.add_value_from_node(ns, node, "./ns:BookgDt/ns:Dt", transaction, "date")
        amount = self.parse_amount(ns, node)
        if amount != 0.0:
            transaction["amount"] = amount
        self.add_value_from_node(
            ns, node, "./ns:AddtlNtryInf", transaction, "payment_ref"
        )
        self.add_value_from_node(
            ns,
            node,
            [
                "./ns:NtryDtls/ns:RmtInf/ns:Strd/ns:CdtrRefInf/ns:Ref",
                "./ns:NtryDtls/ns:Btch/ns:PmtInfId",
                "./ns:NtryDtls/ns:TxDtls/ns:Refs/ns:AcctSvcrRef",
            ],
            transaction["narration"],
            "%s (NtryDtls/Btch/PmtInfId)" % _("Account Servicer Reference"),
        )

        # save AddtlNtryInf for after to add it to name of transaction
        addtl_ntry_inf = node.xpath("./ns:AddtlNtryInf", namespaces={"ns": ns})

        node_charge_amount = node.xpath(
            "./ns:Chrgs/ns:Rcrd/ns:Amt", namespaces={"ns": ns}
        )
        node_charge_included = node.xpath(
            "./ns:Chrgs/ns:Rcrd/ns:ChrgInclInd", namespaces={"ns": ns}
        )

        # has a charge and is not included
        if len(node_charge_included) > 0 and node_charge_included[0].text == "true":
            if len(node_charge_amount) > 0:
                charge_amount = -float(node_charge_amount[0].text)
                tr = transaction.copy()
                tr["amount"] = charge_amount
                tr["payment_ref"] += " (bank charge)"
                yield tr

        # If there is a 'TxDtls' node in the XML we get the value of
        # 'AcctSvcrRef' in it.
        details_nodes = node.xpath("./ns:NtryDtls/ns:TxDtls", namespaces={"ns": ns})
        if len(details_nodes) == 0:
            yield transaction
            self.add_value_from_node(
                ns,
                node,
                "./ns:AcctSvcrRef",
                transaction["narration"],
                "%s (AcctSvcrRef)" % _("Account Servicer Reference"),
            )
            return

        self.add_value_from_node(
            ns,
            node,
            "./ns:BkTxCd/ns:Domn/ns:Fmly/ns:SubFmlyCd",
            transaction["narration"],
            "%s (BkTxCd/Domn/Fmly/SubFmlyCd)" % _("Sub Family Code"),
        )

        self.add_value_from_node(
            ns,
            node,
            "./ns:NtryDtls/ns:TxDtls/ns:Refs/ns:EndToEndId",
            transaction["narration"],
            "%s (NtryDtls/TxDtls/Refs/EndToEndId)" % _("End To End Identification"),
        )

        transaction_base = transaction
        for node in details_nodes:
            transaction = transaction_base.copy()
            self.parse_transaction_details(ns, node, transaction)

            # If there is a AddtlNtryInf, then we do the concatenate
            if addtl_ntry_inf:
                transaction["payment_ref"] += f" - [{addtl_ntry_inf[0].text}]"
            yield transaction
        self.generate_narration(transaction)

    def parse_transaction_details(self, ns, node, transaction):
        super().parse_transaction_details(ns, node, transaction)
        # Check if a global AcctSvcrRef exist
        found_node = node.xpath("../../ns:AcctSvcrRef", namespaces={"ns": ns})
        if len(found_node) != 0:
            self.add_value_from_node(
                ns,
                node,
                "../../ns:AcctSvcrRef",
                transaction["narration"],
                "%s (../../AcctSvcrRef)" % _("Account Servicer Reference"),
            )
        else:
            self.add_value_from_node(
                ns,
                node,
                "./ns:Refs/ns:AcctSvcrRef",
                transaction["narration"],
                "%s (./Refs/AcctSvcrRef)" % _("Account Servicer Reference"),
            )
        # Add transaction note for QR statements
        self.add_value_from_node(
            ns,
            node,
            [
                "./ns:RmtInf/ns:Strd/ns:AddtlRmtInf",
            ],
            transaction,
            "note",
            join_str="\n",
        )

    def parse_statement(self, ns, node):
        result = {}

        iban = node.xpath("./ns:Acct/ns:Id/ns:IBAN", namespaces={"ns": ns})
        if len(iban) > 0:
            # find the journal related to this account
            journals = self.env["account.journal"].search([])
            trans_table = str.maketrans("", "", string.whitespace)
            account_number_ = iban[0].text.translate(trans_table)
            journal = journals.filtered(
                lambda x: x.bank_acc_number
                and x.bank_acc_number.translate(trans_table) == account_number_
                and not x.should_qr_parsing
            )
            if journal:
                self = self.with_context(journal_id=journal.id)

        entry_nodes = node.xpath("./ns:Ntry", namespaces={"ns": ns})
        if len(entry_nodes) > 0:
            result = super().parse_statement(ns, node)

            entry_ref = node.xpath("./ns:Ntry/ns:NtryRef", namespaces={"ns": ns})
            if len(entry_ref) > 1 and "054" in ns:
                first_entry = entry_ref[0].text
                # Parse all entry ref node to check if they're all the same.
                for entry in entry_ref:
                    if first_entry != entry.text:
                        raise ValueError(
                            "Different entry ref in same file " "not supported !"
                        )
            self.add_value_from_node(
                ns, node, "./ns:Ntry/ns:NtryRef", result, "ntryRef"
            )
            result["camt_headers"] = ns
        # In case of an empty camt file
        else:
            result["transactions"] = ""
            result["is_empty"] = True
        return result

    def parse(self, data):
        result = super().parse(data)
        currency = result[0]
        account_number = result[1]
        statements = result[2]
        if len(statements) > 0:
            if "camt_headers" in statements[0]:
                if "camt.054" not in statements[0]["camt_headers"]:
                    statements[0].pop("camt_headers")
                    if "ntryRef" in statements[0]:
                        statements[0].pop("ntryRef")
        return currency, account_number, statements

    def get_balance_amounts(self, ns, node):
        result = super().get_balance_amounts(ns, node)
        start_balance_node = result[0]
        end_balance_node = result[0]

        details_nodes = node.xpath("./ns:Bal/ns:Amt", namespaces={"ns": ns})

        if start_balance_node == 0.0 and not len(details_nodes):
            start_balance_node = node.xpath("./ns:Ntry", namespaces={"ns": ns})
            amount_tot = 0
            for node in start_balance_node:
                amount_tot -= self.parse_amount(ns, node)
            return (amount_tot, end_balance_node)
        return result

    def check_version(self, ns, root):
        try:
            super().check_version(ns, root)
        except ValueError:
            re_camt_version = re.compile(
                r"(^urn:iso:std:iso:20022:tech:xsd:camt.054." r"|^ISO:camt.054.)"
            )
            if not re_camt_version.search(ns):
                raise ValueError("no camt 052 or 053 or 054: " + ns)
            # Check GrpHdr element:
            root_0_0 = root[0][0].tag[len(ns) + 2 :]  # strip namespace
            if root_0_0 != "GrpHdr":
                raise ValueError("expected GrpHdr, got: " + root_0_0)
