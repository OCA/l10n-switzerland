# copyright 2016 Akretion (www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree

from odoo import api, models


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"

    def compute_sepa_final_hook(self, sepa):
        self.ensure_one()
        sepa = super().compute_sepa_final_hook(sepa)
        pain_flavor = self.payment_mode_id.payment_method_id.pain_version
        # ISR orders cannot be SEPA orders
        if pain_flavor and ".ch." in pain_flavor:
            sepa = False
        return sepa

    def generate_pain_nsmap(self):
        self.ensure_one()
        nsmap = super().generate_pain_nsmap()
        pain_flavor = self.payment_mode_id.payment_method_id.pain_version
        if pain_flavor in ["pain.001.001.03.ch.02", "pain.008.001.02.ch.01"]:
            nsmap[None] = (
                "http://www.six-interbank-clearing.com/de/" "%s.xsd" % pain_flavor
            )

        return nsmap

    def generate_pain_attrib(self):
        self.ensure_one()
        pain_flavor = self.payment_mode_id.payment_method_id.pain_version
        if pain_flavor in ["pain.001.001.03.ch.02", "pain.008.001.02.ch.01"]:
            attrib = {
                "{http://www.w3.org/2001/XMLSchema-instance}"
                "schemaLocation": "http://www.six-interbank-clearing.com/de/"
                "%s.xsd  %s.xsd" % (pain_flavor, pain_flavor)
            }
            return attrib
        else:
            return super().generate_pain_attrib()

    @api.model
    def generate_start_payment_info_block(
        self,
        parent_node,
        payment_info_ident,
        priority,
        local_instrument,
        category_purpose,
        sequence_type,
        requested_date,
        eval_ctx,
        gen_args,
    ):
        if gen_args.get("pain_flavor") == "pain.001.001.03.ch.02":
            gen_args["local_instrument_type"] = "proprietary"
            gen_args["structured_remittance_issuer"] = False
        return super().generate_start_payment_info_block(
            parent_node,
            payment_info_ident,
            priority,
            local_instrument,
            category_purpose,
            sequence_type,
            requested_date,
            eval_ctx,
            gen_args,
        )

    @api.model
    def generate_remittance_info_block(self, parent_node, line, gen_args):
        if line.payment_line_ids[:1].communication_type == "qrr":
            remittance_info = etree.SubElement(parent_node, "RmtInf")
            remittance_info_structured = etree.SubElement(remittance_info, "Strd")
            creditor_ref_information = etree.SubElement(
                remittance_info_structured, "CdtrRefInf"
            )
            creditor_ref_info_type = etree.SubElement(creditor_ref_information, "Tp")
            creditor_ref_info_type_or = etree.SubElement(
                creditor_ref_info_type, "CdOrPrtry"
            )
            creditor_ref_info_type_code = etree.SubElement(
                creditor_ref_info_type_or, "Prtry"
            )
            creditor_ref_info_type_code.text = "QRR"
            creditor_reference = etree.SubElement(creditor_ref_information, "Ref")
            creditor_reference.text = line.payment_line_ids[0].communication
            return True
        else:
            return super().generate_remittance_info_block(parent_node, line, gen_args)
