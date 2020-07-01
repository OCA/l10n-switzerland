##############################################################################
#
#    Swiss localization Direct Debit module for OpenERP
#    Copyright (C) 2014 Compassion (http://www.compassion.ch)
#    Copyright (C) 2017 brain-tec AG (http://www.braintec-group.com)
#    @author: Cyril Sester <cyril.sester@outlook.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, api, _
from lxml import etree
from odoo.tools import float_round
from odoo import fields

ACCEPTED_PAIN_FLAVOURS = (
    'pain.008.001.02.ch.03',
)


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    @api.multi
    def show_invoices(self):
        return {
            'name': _('Related invoices'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('move_id', 'in', self.mapped(
                'payment_line_ids.move_line_id.move_id').ids)],
            'res_model': 'account.invoice',
            'target': 'current',
        }

    @api.multi
    def generate_payment_file(self):
        """ Overridden to consider XML-DD.
            Returns (payment file as string, filename)
        """
        self.ensure_one()

        pain_flavor = self.payment_method_id.pain_version

        # We are going to re-use the wizard, thus we pass the
        # active_ids through the context.
        new_context = self._context.copy()
        new_context.update({'active_ids': self.ids})

        if pain_flavor in ACCEPTED_PAIN_FLAVOURS:
            file_content, file_name = self.generate_xml_ch_dd_file()
            res = file_content, file_name
        else:
            res = super(AccountPaymentOrder, self).generate_payment_file()

        return res

    @api.multi
    def generate_pain_nsmap(self):
        self.ensure_one()
        nsmap = super(AccountPaymentOrder, self).generate_pain_nsmap()
        pain_flavor = self.payment_mode_id.payment_method_id.pain_version
        if pain_flavor in ACCEPTED_PAIN_FLAVOURS:
            nsmap[None] = 'http://www.six-interbank-clearing.com/de/%s.xsd' % \
                          pain_flavor
        return nsmap

    @api.multi
    def generate_pain_attrib(self):
        self.ensure_one()
        pain_flavor = self.payment_mode_id.payment_method_id.pain_version
        if pain_flavor in ACCEPTED_PAIN_FLAVOURS:
            attrib = {
                "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation":
                "http://www.six-interbank-clearing.com/de/%s.xsd  %s.xsd" %
                (pain_flavor, pain_flavor)
            }
        else:
            attrib = super(AccountPaymentOrder, self).generate_pain_attrib()
        return attrib

    @api.model
    def _must_have_initiating_party(self, gen_args):
        if gen_args.get('pain_flavor') in ACCEPTED_PAIN_FLAVOURS:
            return True
        else:
            return super(AccountPaymentOrder, self).\
                _must_have_initiating_party(gen_args)

    @api.model
    def generate_group_header_block(self, parent_node, gen_args):
        group_header, nb_of_transactions_a, control_sum_a = \
            super(AccountPaymentOrder, self).generate_group_header_block(
                parent_node, gen_args)

        if gen_args.get('pain_flavor') in ACCEPTED_PAIN_FLAVOURS:
            # It removes the tag <Issr> and its subtree.
            subtrees = group_header.xpath('//Issr')
            for subtree in subtrees:
                subtree.getparent().remove(subtree)

        return group_header, nb_of_transactions_a, control_sum_a

    @api.model
    def generate_start_payment_info_block(
        self, parent_node, payment_info_ident,
        priority, local_instrument, category_purpose, sequence_type,
            requested_date, sepa, eval_ctx, gen_args):
        """ This is overridden because pain.008.001.03.ch.01 uses a different
            XML structure. The code is basically the same that can be found
            on the module account_banking_pain_base's method
            generate_start_payment_info_block().
        """

        if gen_args.get('pain_flavor') in ACCEPTED_PAIN_FLAVOURS:
            payment_info = etree.SubElement(parent_node, 'PmtInf')

            # <PmtInf>/  <PmtInfId>
            payment_info_identification = \
                etree.SubElement(payment_info, 'PmtInfId')
            payment_info_identification.text = self._prepare_field(
                'Payment Information Identification',
                payment_info_ident, eval_ctx, 35, gen_args=gen_args)

            # <PmtInf>/  <PmtMtd>
            payment_method = etree.SubElement(payment_info, 'PmtMtd')
            payment_method.text = gen_args['payment_method']

            # These two parameters are set to False only to avoid changing the
            # return of the method we are overriding.
            nb_of_transactions = False
            control_sum = False

            # <PmtInf>/  <PmtTpInf>
            payment_type_info = etree.SubElement(payment_info, 'PmtTpInf')
            if priority and gen_args['payment_method'] != 'DD':
                instruction_priority = \
                    etree.SubElement(payment_type_info, 'InstrPrty')
                instruction_priority.text = priority

            # <PmtInf>/<PmtTpInf>/  <SvcLvl>
            service_level = etree.SubElement(payment_type_info, 'SvcLvl')

            # <PmtInf>/<PmtTpInf>/  <LclInstrm>
            local_instrument_root = etree.SubElement(payment_type_info,
                                                     'LclInstrm')
            # <PmtInf>/<PmtTpInf>/<SvcLvl>/  <Prtry>
            if self.company_partner_bank_id.acc_type in ('postal', 'iban'):
                service_level_value = etree.SubElement(service_level, 'Prtry')
                local_instr_value = \
                    etree.SubElement(local_instrument_root, 'Prtry')
                if self.company_partner_bank_id.acc_type == 'postal' or \
                   self.company_partner_bank_id.bank_id.bic == 'POFICHBEXXX':
                    prtry_value = 'CHDD'
                else:
                    prtry_value = 'CHTA'
                    for line in self.bank_line_ids:
                        line.local_instrument = local_instrument
                service_level_value.text = prtry_value
                local_instr_value.text = local_instrument

            # <PmtInf>/<PmtTpInf>/  <ReqdColltnDt>
            requested_date_node = etree.SubElement(payment_info,
                                                   'ReqdColltnDt')
            requested_date_node.text = fields.Date.to_string(requested_date)

        else:
            payment_info, nb_of_transactions, control_sum = \
                super(AccountPaymentOrder, self).\
                generate_start_payment_info_block(
                    parent_node, payment_info_ident,
                    priority, local_instrument, category_purpose,
                    sequence_type, requested_date, sepa, eval_ctx, gen_args)

        return payment_info, nb_of_transactions, control_sum

    @api.model
    def generate_party_acc_number(
            self, parent_node, party_type, order, partner_bank, gen_args,
            bank_line=None):
        if gen_args.get('pain_flavor') in ACCEPTED_PAIN_FLAVOURS:
            # <CdtrAcct>
            party_account = etree.SubElement(parent_node,
                                             '%sAcct' % party_type)
            party_account_id = etree.SubElement(party_account, 'Id')
            party_account_iban = etree.SubElement(party_account_id, 'IBAN')
            party_account_iban.text = partner_bank.acc_number.replace(' ', '')
            res = True
        else:
            res = super(AccountPaymentOrder, self).generate_party_acc_number(
                parent_node, party_type, order, partner_bank, gen_args,
                bank_line)

        return res

    @api.model
    def generate_party_agent(
            self, parent_node, party_type, order, partner_bank, gen_args,
            bank_line=None):
        if gen_args.get('pain_flavor') in ACCEPTED_PAIN_FLAVOURS:
            party_agent = etree.SubElement(parent_node, '%sAgt' % party_type)
            party_agent_institution = \
                etree.SubElement(party_agent, 'FinInstnId')

            # <CdtrAgt>/<FinInstnId>/  <ClrSysMmbId>
            party_agent_clearing = \
                etree.SubElement(party_agent_institution, 'ClrSysMmbId')
            party_agent_clearing_identification = \
                etree.SubElement(party_agent_clearing, 'MmbId')
            party_agent_clearing_identification.text = \
                partner_bank.bank_id.clearing.zfill(5)
            ccp_other = etree.SubElement(party_agent_institution, 'Othr')
            ccp_other_id = etree.SubElement(ccp_other, 'Id')
            ref_subparts = self.company_partner_bank_id.l10n_ch_postal.split('-')
            ccp_other_id.text = (
                ref_subparts[0] + ref_subparts[1].rjust(6, '0') + ref_subparts[2]
            )

            res = True
        else:
            res = super(AccountPaymentOrder, self).generate_party_agent(
                parent_node, party_type, order, partner_bank, gen_args,
                bank_line)
        return res

    @api.model
    def generate_party_block(
            self, parent_node, party_type, order, partner_bank, gen_args,
            bank_line=None):
        """ This is overridden because pain.008.001.02.ch.03 uses a
            different XML structure. The code is basically the same that
            can be found on the module account_banking_pain_base's method
            generate_party_block().
        """
        if gen_args.get('pain_flavor') in ACCEPTED_PAIN_FLAVOURS:

            # <Cdtr>
            party = etree.SubElement(parent_node, party_type)

            if party_type == 'Cdtr':
                party_type_label = 'Creditor'
            elif party_type == 'Dbtr':
                party_type_label = 'Debtor'

            name = 'partner_bank.partner_id.name'
            eval_ctx = {'partner_bank': partner_bank}
            party_name = self._prepare_field('%s Name' % party_type_label,
                                             name, eval_ctx,
                                             gen_args.get('name_maxsize'),
                                             gen_args=gen_args)

            # <Cdtr>/  <Nm>
            party_nm = etree.SubElement(party, 'Nm')
            party_nm.text = party_name
            partner = partner_bank.partner_id

            if partner.country_id:
                # <Cdtr>/<Nm>/  <PstlAdr>
                postal_address = etree.SubElement(party, 'PstlAdr')

                # <Cdtr>/<Nm>/  <Ctry>
                country = etree.SubElement(postal_address, 'Ctry')
                country.text = self._prepare_field('Country',
                                                   'partner.country_id.code',
                                                   {'partner': partner}, 2,
                                                   gen_args=gen_args)

                # <Cdtr>/<Nm>/  <AdrLine> x2
                if partner.street:
                    adrline1 = etree.SubElement(postal_address, 'AdrLine')
                    adrline1.text =\
                        self._prepare_field('Adress Line1',
                                            'partner.street',
                                            {'partner': partner},
                                            70, gen_args=gen_args)
                if partner.city and partner.zip:
                    adrline2 = etree.SubElement(postal_address, 'AdrLine')
                    adrline2.text = \
                        self._prepare_field('Address Line2',
                                            "partner.zip + ' ' + partner.city",
                                            {'partner': partner}, 70,
                                            gen_args=gen_args)

            # <CdtrAcct>
            self.generate_party_acc_number(parent_node, party_type, order,
                                           partner_bank, gen_args,
                                           bank_line=bank_line)

            if order == 'B':
                self.generate_party_agent(
                    parent_node, party_type, order, partner_bank, gen_args,
                    bank_line=bank_line)

            res = True

        else:
            res = super(AccountPaymentOrder, self).generate_party_block(
                parent_node, party_type, order, partner_bank,
                gen_args, bank_line)

        return res

    @api.multi
    def generate_dd_transaction_information(self, parent_node, partner_bank,
                                            lines, gen_args):
        """ Takes portions of the code that is inside
            account_banking_sepa_direct_debit's generate_payment_file().
            Implements the //<DrctDbtTxInf> part of the XML
            for pain.008.001.03.ch.01.
        """
        for line in lines:

            dd_transaction_info = etree.SubElement(
                parent_node, 'DrctDbtTxInf')
            payment_identification = etree.SubElement(
                dd_transaction_info, 'PmtId')
            instruction_identification = etree.SubElement(
                payment_identification, 'InstrId')
            instruction_identification.text = self._prepare_field(
                'Intruction Identification', 'line.name',
                {'line': line}, 35, gen_args=gen_args)
            end2end_identification = etree.SubElement(
                payment_identification, 'EndToEndId')
            end2end_identification.text = self._prepare_field(
                'End to End Identification', 'line.name',
                {'line': line}, 35, gen_args=gen_args)
            currency_name = self._prepare_field(
                'Currency Code', 'line.currency_id.name',
                {'line': line}, 3, gen_args=gen_args)
            instructed_amount = etree.SubElement(
                dd_transaction_info, 'InstdAmt', Ccy=currency_name)
            instructed_amount.text = '%.2f' % line.amount_currency

            # .../  <DbtrAgt>
            ori_debtor_agent = etree.SubElement(
                dd_transaction_info, 'DbtrAgt')
            ori_debtor_agent_institution = etree.SubElement(
                ori_debtor_agent, 'FinInstnId')
            ori_debtor_agent_institution_clearing = etree.SubElement(
                ori_debtor_agent_institution, 'ClrSysMmbId')
            ori_debtor_agent_institution_clearing_identification =\
                etree.SubElement(ori_debtor_agent_institution_clearing,
                                 'MmbId')
            ori_debtor_agent_institution_clearing_identification.text = \
                line.partner_bank_id.bank_id.clearing.zfill(5)

            # .../  <Dbtr>
            self.generate_party_block(
                dd_transaction_info, 'Dbtr', 'C',
                line.partner_bank_id, gen_args, line)

            # .../  <DbtrAcct>
            dbtr_acct = etree.Element("DbtrAcct")
            dbtr_acct_id = etree.SubElement(dbtr_acct, "Id")
            dbtr_acct_iban = etree.SubElement(dbtr_acct_id, "IBAN")
            dbtr_acct_iban.text = partner_bank.acc_number.replace(' ', '')

            # .../  <RmtInf>
            self.generate_remittance_info_block(dd_transaction_info,
                                                line, gen_args)

        return True

    @api.model
    def generate_remittance_info_block(self, parent_node, line, gen_args):
        if line.local_instrument == "LSV+":
            remittance_info = etree.SubElement(
                parent_node, 'RmtInf')
            remittance_info_unstructured = etree.SubElement(
                remittance_info, 'Ustrd')
            remittance_info_unstructured.text = self._prepare_field(
                'Remittance Unstructured Information',
                'line.communication', {'line': line}, 140,
                gen_args=gen_args)
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
            creditor_ref_info_type_code.text = 'ESR'
            creditor_reference = etree.SubElement(
                creditor_ref_information, 'Ref')
            creditor_reference.text = line.payment_line_ids[0].communication
        else:
            super().generate_remittance_info_block(parent_node, line, gen_args)

    @api.multi
    def generate_xml_ch_dd_file(self):
        self.ensure_one()

        pay_method = self.payment_mode_id.payment_method_id
        xsd_file = pay_method.get_xsd_file_path()
        gen_args = {
            'bic_xml_tag': 'BIC',
            'name_maxsize': 70,
            'convert_to_ascii': pay_method.convert_to_ascii,
            'payment_method': 'DD',
            'file_prefix': 'sdd_',
            'pain_flavor': pay_method.pain_version,
            'pain_xsd_file': xsd_file,
        }

        # Creates the container tag, with the schema and so on.
        nsmap = self.generate_pain_nsmap()
        attrib = self.generate_pain_attrib()
        xml_root = etree.Element('Document', nsmap=nsmap, attrib=attrib)

        # Creates the root tag <CstmrDrctDbtInitn> having the content.
        root = etree.SubElement(xml_root, 'CstmrDrctDbtInitn')

        # Creates the header tag <GrpHdr>
        group_header, nb_of_transactions_a, control_sum_a = \
            self.generate_group_header_block(root, gen_args)

        # The following code is very much inspired from
        # that of account_banking_sepa_credit_transfer.

        lines_per_group = {}
        for line in self.bank_line_ids:
            key = (line.date, line.priority, line.local_instrument)
            lines_per_group.setdefault(key, []).append(line)

        index = 0
        for (req_date, prio, local_inst), lines in \
                list(lines_per_group.items()):
            # Creates the tags <PmtInf>/  [<PmtInfId>, <PmtMtd>,
            # <PmtTpInf>, <ReqdColltnDt>]
            payment_info, nb_of_transactions_b, control_sum_b = \
                self.generate_start_payment_info_block(
                    root,
                    "self.name + '-' "
                    "+ str(requested_date) + '-' + priority + "
                    "'-' + local_instrument",
                    prio, local_inst, False, False, req_date, False, eval_ctx={
                        'self': self,
                        'priority': prio,
                        'requested_date': req_date,
                        'local_instrument': local_inst or 'NOinstr',
                    }, gen_args=gen_args)

            # Creates the tags <PmtInf>/  [<Cdtr>, <CdtrAcct>, <CdtrAgt>]
            self.generate_party_block(payment_info, 'Cdtr', 'B',
                                      self.company_partner_bank_id, gen_args)

            # <PmtInf>/  <CdtrSchmeId>
            creditor_scheme_identification = \
                etree.SubElement(payment_info, 'CdtrSchmeId')

            if not local_inst:
                local_inst = lines[index].local_instrument

            scheme_name_proprietary = ""
            if local_inst == "DDCOR1":
                scheme_name_proprietary = "CHDD"
            elif local_inst == "LSV+":
                scheme_name_proprietary = "CHLS"

            self.generate_creditor_scheme_identification(
                creditor_scheme_identification,
                'self.payment_mode_id.initiating_party_identifier or '
                'self.company_id.initiating_party_identifier',
                'SEPA Creditor Identifier', {'self': self},
                scheme_name_proprietary, gen_args)

            # <PmtInf>/  <DrctDbtTxInf>
            self.generate_dd_transaction_information(
                payment_info, self.company_partner_bank_id, lines, gen_args)
            index = index + 1

        # It sets the number of transactions, <NbOfTxs>
        nb_of_transactions_a.text = str(len(self.bank_line_ids))

        # It sets the check sum, <CtrlSum>
        ctrl_sum = float_round(sum(bank_line.amount_currency
                                   for bank_line in self.bank_line_ids), 2)
        control_sum_a.text = str(ctrl_sum)

        return self.finalize_sepa_file_creation(xml_root, gen_args)
