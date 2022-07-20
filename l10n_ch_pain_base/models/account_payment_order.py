# copyright 2016 Akretion (www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, _
from odoo.exceptions import UserError
from lxml import etree


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    @api.multi
    def compute_sepa_final_hook(self, sepa):
        self.ensure_one()
        sepa = super().compute_sepa_final_hook(sepa)
        pain_flavor = self.payment_mode_id.payment_method_id.pain_version

        if pain_flavor and '.ch.' in pain_flavor:
            # If all payments are made to Swiss IBANs, it's a domestic order
            acc_numbers = self.payment_line_ids.mapped(
                'partner_bank_id.acc_number')
            acc_numbers = list(set([x[0:2] for x in acc_numbers]))
            if acc_numbers == ['CH']:
                return False

            # ISR orders cannot be SEPA orders
            instrs = self.payment_line_ids.mapped('local_instrument')
            if 'CH01' in instrs:
                return False
        return sepa

    @api.multi
    def generate_pain_nsmap(self):
        self.ensure_one()
        nsmap = super().generate_pain_nsmap()
        pain_flavor = self.payment_mode_id.payment_method_id.pain_version
        if pain_flavor in ['pain.001.001.03.ch.02', 'pain.008.001.02.ch.01']:
            nsmap[None] = 'http://www.six-interbank-clearing.com/de/'\
                          '%s.xsd' % pain_flavor

        return nsmap

    @api.multi
    def generate_pain_attrib(self):
        self.ensure_one()
        pain_flavor = self.payment_mode_id.payment_method_id.pain_version
        if pain_flavor in ['pain.001.001.03.ch.02', 'pain.008.001.02.ch.01']:
            attrib = {
                "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation":
                "http://www.six-interbank-clearing.com/de/"
                "%s.xsd  %s.xsd" % (pain_flavor, pain_flavor)
                }
            return attrib
        else:
            return super().generate_pain_attrib()

    @api.model
    def generate_start_payment_info_block(
            self, parent_node, payment_info_ident,
            priority, local_instrument, category_purpose, sequence_type,
            requested_date, eval_ctx, gen_args):
        if gen_args.get('pain_flavor') == 'pain.001.001.03.ch.02':
            gen_args['local_instrument_type'] = 'proprietary'
            gen_args['structured_remittance_issuer'] = False
        return super().generate_start_payment_info_block(
            parent_node, payment_info_ident, priority, local_instrument,
            category_purpose, sequence_type, requested_date, eval_ctx,
            gen_args,
        )

    @api.model
    def generate_party_agent(
            self, parent_node, party_type, order, partner_bank, gen_args,
            bank_line=None):
        if (
                gen_args.get('pain_flavor') == 'pain.001.001.03.ch.02' and
                bank_line):
            if bank_line.local_instrument == 'CH01':
                # Don't set the creditor agent on ISR/CH01 payments
                return True
            elif not partner_bank.bank_bic:
                raise UserError(_(
                    "For pain.001.001.03.ch.02, for non-ISR payments, "
                    "the BIC is required on the bank '%s' related to the "
                    "bank account '%s'") % (
                        partner_bank.bank_id.name,
                        partner_bank.acc_number))
        assert order in ('B', 'C'), "Order can be 'B' or 'C'"
        party_agent = etree.SubElement(parent_node, '%sAgt' % party_type)
        party_agent_institution = etree.SubElement(party_agent, 'FinInstnId')
        if partner_bank.bank_bic:
            party_agent_bic = etree.SubElement(
                party_agent_institution, gen_args.get('bic_xml_tag'))
            party_agent_bic.text = partner_bank.bank_bic
        else:
            if order == 'B' or (
                    order == 'C' and gen_args['payment_method'] == 'DD'):
                if partner_bank.type == 'iban':
                    iban = partner_bank.sanitized_acc_number
                    abi_code = iban[5:10]
                party_agent_sys_mmb_id = etree.SubElement(
                    party_agent_institution, 'ClrSysMmbId')

                member_identification = etree.SubElement(
                    party_agent_sys_mmb_id, 'MmbId')
                member_identification.text = abi_code
            # for Credit Transfers, in the 'C' block, if BIC is not provided,
            # we should not put the 'Creditor Agent' block at all,
            # as per the guidelines of the EPC
        return True

    @api.model
    def generate_party_acc_number(self, parent_node, party_type, order,
                                  partner_bank, gen_args, bank_line=None):
        if (gen_args.get('pain_flavor') == 'pain.001.001.03.ch.02' and
                bank_line and
                bank_line.local_instrument == 'CH01'):
            if not partner_bank.ccp:
                raise UserError(_(
                    "The field 'CCP/CP-Konto' is not set on the bank "
                    "account '%s'.") % partner_bank.acc_number)
            party_account = etree.SubElement(
                parent_node, '%sAcct' % party_type)
            party_account_id = etree.SubElement(party_account, 'Id')
            party_account_other = etree.SubElement(
                party_account_id, 'Othr')
            party_account_other_id = etree.SubElement(
                party_account_other, 'Id')
            party_account_other_id.text = partner_bank.ccp
            return True
        else:
            return super().generate_party_acc_number(
                parent_node, party_type, order, partner_bank, gen_args,
                bank_line=bank_line)

    @api.model
    def generate_address_block(
            self, parent_node, partner, gen_args):
        """Generate the piece of the XML corresponding to PstlAdr"""
        if partner.country_id:
            postal_address = etree.SubElement(parent_node, 'PstlAdr')

            country = etree.SubElement(postal_address, 'Ctry')
            country.text = self._prepare_field(
                'Country', 'partner.country_id.code',
                {'partner': partner}, 2, gen_args=gen_args)

            if partner.street or partner.street2:
                adrline1 = etree.SubElement(postal_address, 'AdrLine')
                adrline1.text = ', '.join(
                    filter(None, [partner.street, partner.street2])
                )

                if partner.zip and partner.city:
                    adrline2 = etree.SubElement(postal_address, 'AdrLine')
                    adrline2.text = ' '.join([partner.zip, partner.city])

        return True
<<<<<<< HEAD
=======

    @api.model
    def generate_remittance_info_block(self, parent_node, line, gen_args):
        if line.communication_type == "qrr":
            remittance_info = etree.SubElement(
                parent_node, 'RmtInf')
            remittance_info_structured = etree.SubElement(
                remittance_info, 'Strd')
            creditor_ref_information = etree.SubElement(
                remittance_info_structured, 'CdtrRefInf')
            creditor_ref_info_type = etree.SubElement(
                creditor_ref_information, 'Tp')
            creditor_ref_info_type_or = etree.SubElement(
                creditor_ref_info_type, 'CdOrPrtry')
            creditor_ref_info_type_code = etree.SubElement(
                creditor_ref_info_type_or, 'Prtry')
            creditor_ref_info_type_code.text = 'QRR'
            creditor_reference = etree.SubElement(
                creditor_ref_information, 'Ref')
            creditor_reference.text = line.payment_line_ids[0].communication
        else:
            super().generate_remittance_info_block(parent_node, line, gen_args)
>>>>>>> 4c44a9ec... [MIG][l10n_ch_pain_base] Backport of feature from v. 12.0
