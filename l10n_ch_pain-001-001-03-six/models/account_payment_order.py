# Copyright 2010-2020 Akretion (www.akretion.com)
# Copyright 2014-2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from lxml import etree

from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"

    def generate_payment_file(self):  # noqa: C901
        """Creates the SEPA Credit Transfer file. That's the important code!"""
        print("l10n_ch_pain-001-001-03-six/models/account_payment_order.py generate_payment_file")
        self.ensure_one()
        if self.payment_method_id.code != "sepa_credit_transfer_chf":
            return super().generate_payment_file()

        pain_flavor = self.payment_method_id.pain_version
        # We use pain_flavor.startswith('pain.001.001.xx')
        # to support country-specific extensions such as
        # pain.001.001.03.ch.02 (cf l10n_ch_sepa)
        if not pain_flavor:
            raise UserError(_("pain_version is not set in payment_method '%s'.")
                               % self.payment_method_id.code)
        if pain_flavor.startswith("pain.001.001.03.ch.02"):
            bic_xml_tag = "BIC"
            # size 70 -> 140 for <Nm> with pain.001.001.03
            # BUT CH definition:
            # Name of the message sender, maximum 70 characters.
            name_maxsize = 70
            root_xml_tag = "CstmrCdtTrfInitn"
        else:
            raise UserError(_("PAIN version '%s' is not supported.") % pain_flavor)
        xsd_file = self.payment_method_id.get_xsd_file_path()
        gen_args = {
            "bic_xml_tag": bic_xml_tag,
            "name_maxsize": name_maxsize,
            "convert_to_ascii": self.payment_method_id.convert_to_ascii,
            "payment_method": "TRF",
            "file_prefix": "sct_",
            "pain_flavor": pain_flavor,
            "pain_xsd_file": xsd_file,
        }
        nsmap = self.generate_pain_nsmap()
        attrib = self.generate_pain_attrib()
        xml_root = etree.Element("Document", nsmap=nsmap, attrib=attrib)
        pain_root = etree.SubElement(xml_root, root_xml_tag)
        # A. Group header
        header = self.generate_group_header_block(pain_root, gen_args)
        group_header, nb_of_transactions_a, control_sum_a = header
        transactions_count_a = 0
        amount_control_sum_a = 0.0
        lines_per_group = {}
        # key = (requested_date, priority, local_instrument, categ_purpose)
        # values = list of lines as object
        for line in self.bank_line_ids:
            priority = line.priority
            local_instrument = line.local_instrument
            categ_purpose = line.category_purpose
            # The field line.date is the requested payment date
            # taking into account the 'date_prefered' setting
            # cf account_banking_payment_export/models/account_payment.py
            # in the inherit of action_open()
            key = (line.date, priority, local_instrument, categ_purpose)
            if key in lines_per_group:
                lines_per_group[key].append(line)
            else:
                lines_per_group[key] = [line]
        for (requested_date, priority, local_instrument, categ_purpose), lines in list(
            lines_per_group.items()
        ):
            # B. Payment info
            requested_date = fields.Date.to_string(requested_date)
            (
                payment_info,
                nb_of_transactions_b,
                control_sum_b,
            ) = self.generate_start_payment_info_block(
                pain_root,
                "self.name + '-' "
                "+ requested_date.replace('-', '')  + '-' + priority + "
                "'-' + local_instrument + '-' + category_purpose",
                priority,
                local_instrument,
                categ_purpose,
                False,
                requested_date,
                {
                    "self": self,
                    "priority": priority,
                    "requested_date": requested_date,
                    "local_instrument": local_instrument or "NOinstr",
                    "category_purpose": categ_purpose or "NOcateg",
                },
                gen_args,
            )
            self.generate_party_block(
                payment_info, "Dbtr", "B", self.company_partner_bank_id, gen_args
            )
            charge_bearer = etree.SubElement(payment_info, "ChrgBr")
            if self.sepa:
                charge_bearer_text = "SLEV"
            else:
                charge_bearer_text = self.charge_bearer
            charge_bearer.text = charge_bearer_text
            transactions_count_b = 0
            amount_control_sum_b = 0.0
            for line in lines:
                transactions_count_a += 1
                transactions_count_b += 1
                # C. Credit Transfer Transaction Info
                credit_transfer_transaction_info = etree.SubElement(
                    payment_info, "CdtTrfTxInf"
                )
                payment_identification = etree.SubElement(
                    credit_transfer_transaction_info, "PmtId"
                )
                instruction_identification = etree.SubElement(
                    payment_identification, "InstrId"
                )
                instruction_identification.text = self._prepare_field(
                    "Instruction Identification",
                    "line.name",
                    {"line": line},
                    35,
                    gen_args=gen_args,
                )
                end2end_identification = etree.SubElement(
                    payment_identification, "EndToEndId"
                )
                end2end_identification.text = self._prepare_field(
                    "End to End Identification",
                    "line.name",
                    {"line": line},
                    35,
                    gen_args=gen_args,
                )

                ### CH definition: Is currently ignored by financial institutions.
                # currency_name = self._prepare_field(
                #     "Currency Code",
                #     "line.currency_id.name",
                #     {"line": line},
                #     3,
                #     gen_args=gen_args,
                # )
                amount = etree.SubElement(credit_transfer_transaction_info, "Amt")
                instructed_amount = etree.SubElement(
                    amount, "InstdAmt", Ccy=currency_name
                )
                instructed_amount.text = "%.2f" % line.amount_currency
                amount_control_sum_a += line.amount_currency
                amount_control_sum_b += line.amount_currency
                if not line.partner_bank_id:
                    raise UserError(
                        _(
                            "Bank account is missing on the bank payment line "
                            "of partner '{partner}' (reference '{reference}')."
                        ).format(partner=line.partner_id.name, reference=line.name)
                    )

                self.generate_party_block(
                    credit_transfer_transaction_info,
                    "Cdtr",
                    "C",
                    line.partner_bank_id,
                    gen_args,
                    line,
                )
                if line.purpose:
                    purpose = etree.SubElement(credit_transfer_transaction_info, "Purp")
                    etree.SubElement(purpose, "Cd").text = line.purpose
                self.generate_remittance_info_block(
                    credit_transfer_transaction_info, line, gen_args
                )
        nb_of_transactions_a.text = str(transactions_count_a)
        control_sum_a.text = "%.2f" % amount_control_sum_a
        return self.finalize_sepa_file_creation(xml_root, gen_args)
