# copyright 2016 Akretion (www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree

from odoo import _, api, models
from odoo.exceptions import UserError

ACCEPTED_PAIN_FLAVOURS = ("pain.001.001.03.ch.02", "pain.008.001.02.ch.03")

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
        if pain_flavor in ACCEPTED_PAIN_FLAVOURS:
            nsmap[None] = (
                "http://www.six-interbank-clearing.com/de/%s.xsd" % pain_flavor
            )

        return nsmap

    def generate_pain_attrib(self):
        self.ensure_one()
        pain_flavor = self.payment_mode_id.payment_method_id.pain_version
        if pain_flavor in ACCEPTED_PAIN_FLAVOURS:
            attrib = {
            "{http://www.w3.org/2001/XMLSchema-instance}"
            "schemaLocation": "http://www.six-interbank-clearing.com/de/%s.xsd  %s.xsd"
                              % (pain_flavor, pain_flavor)
            }
            return attrib
        else:
            return super().generate_pain_attrib()


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
            # to uncomment when schema pain.001.001.09.ch.03 is implemented in account_banking_pain_base
            # remittance_info_structured = etree.SubElement(remittance_info, "AddtlRmtInf")
            # remittance_info_structured.text = line.payment_line_ids[0].move_line_id.move_id.ref or ""
        else:
            super().generate_remittance_info_block(parent_node, line, gen_args)
