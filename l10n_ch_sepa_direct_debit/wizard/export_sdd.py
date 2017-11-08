# -*- coding: utf-8 -*-
##############################################################################
#
#    SEPA Direct Debit module for OpenERP
#    Copyright (C) 2010-2013 Akretion (http://www.akretion.com)
#    @author: Anar Baghirli <a.baghirli.mobilunity.com>
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

from openerp.osv import orm, fields
from openerp.tools.translate import _
from lxml import etree


class BankingExportSepaWizard(orm.TransientModel):
    _inherit = 'banking.export.sdd.wizard'

    def generate_party_block(
            self, cr, uid, parent_node, party_type, order, name, iban, bic,
            eval_ctx, gen_args, context=None):
        '''Generate the piece of the XML file corresponding to Name+IBAN+BIC
        This code is mutualized between TRF and DD'''
        assert order in ('B', 'C'), "Order can be 'B' or 'C'"
        if party_type == 'Cdtr':
            party_type_label = 'Creditor'
        elif party_type == 'Dbtr':
            party_type_label = 'Debtor'
        party_name = self._prepare_field(
            cr, uid, '%s Name' % party_type_label, name, eval_ctx,
            gen_args.get('name_maxsize'),
            gen_args=gen_args, context=context)
        piban = self._prepare_field(
            cr, uid, '%s IBAN' % party_type_label, iban, eval_ctx,
            gen_args=gen_args,
            context=context)
        if 'sepa_export' in eval_ctx:
            if eval_ctx['sepa_export'].payment_order_ids[0].\
                    mode.bank_id.state == 'iban':
                viban = self._validate_iban(cr, uid, piban, context=context)
            else:
                viban = piban
        if 'line' in eval_ctx:
            if eval_ctx['line'].bank_id.state == 'iban':
                viban = self._validate_iban(cr, uid, piban, context=context)
            else:
                viban = piban
        # At C level, the order is : BIC, Name, IBAN
        # At B level, the order is : Name, IBAN, BIC
        if order == 'B':
            gen_args['initiating_party_country_code'] = viban[0:2]
        elif order == 'C':
            self.generate_party_agent(
                cr, uid, parent_node, party_type, party_type_label,
                order, party_name, viban, bic,
                eval_ctx, gen_args, context=context)
        party = etree.SubElement(parent_node, party_type)
        party_nm = etree.SubElement(party, 'Nm')
        party_nm.text = party_name
        party_account = etree.SubElement(
            parent_node, '%sAcct' % party_type)
        party_account_id = etree.SubElement(party_account, 'Id')
        if 'sepa_export' in eval_ctx:
            if eval_ctx['sepa_export'].payment_order_ids[0].\
                    mode.bank_id.state == 'iban':
                party_account_iban = etree.SubElement(
                    party_account_id, 'IBAN')
                party_account_iban.text = viban
            else:
                party_account_iban = etree.SubElement(
                    party_account_id, 'Othr')
                party_account_iban.text = viban
        if 'line' in eval_ctx:
            if eval_ctx['line'].bank_id.state == 'iban':
                party_account_iban = etree.SubElement(
                    party_account_id, 'IBAN')
                party_account_iban.text = viban
            else:
                party_account_iban = etree.SubElement(
                    party_account_id, 'Othr')
                party_account_othr_id = etree.SubElement(
                    party_account_iban, 'Id')
                party_account_othr_id.text = viban
        if order == 'B':
            self.generate_party_agent(
                cr, uid, parent_node, party_type, party_type_label,
                order, party_name, viban, bic,
                eval_ctx, gen_args, context=context)
        return True

    def create_sepa(self, cr, uid, ids, context=None):
        '''
        Creates the SEPA Direct Debit file. That's the important code !
        '''
        sepa_export = self.browse(cr, uid, ids[0], context=context)

        pain_flavor = sepa_export.payment_order_ids[0].mode.type.code
        convert_to_ascii = \
            sepa_export.payment_order_ids[0].mode.convert_to_ascii
        if pain_flavor == 'pain.008.001.02':
            bic_xml_tag = 'BIC'
            name_maxsize = 70
            root_xml_tag = 'CstmrDrctDbtInitn'
        elif pain_flavor == 'pain.008.001.03':
            bic_xml_tag = 'BICFI'
            name_maxsize = 140
            root_xml_tag = 'CstmrDrctDbtInitn'
        elif pain_flavor == 'pain.008.001.04':
            bic_xml_tag = 'BICFI'
            name_maxsize = 140
            root_xml_tag = 'CstmrDrctDbtInitn'
        elif pain_flavor == 'pain.008.001.02.ch.01':
            bic_xml_tag = 'BIC'
            name_maxsize = 140
            root_xml_tag = 'CstmrDrctDbtInitn'
        else:
            raise orm.except_orm(
                _('Error:'),
                _("Payment Type Code '%s' is not supported. The only "
                  "Payment Type Code supported for SEPA Direct Debit "
                  "are 'pain.008.001.02', 'pain.008.001.03' and "
                  "'pain.008.001.04'.") % pain_flavor)

        if pain_flavor == 'pain.008.001.02.ch.01':
            module = 'l10n_ch_sepa_direct_debit'
        else:
            module = 'account_banking_sepa_direct_debit'
        gen_args = {
            'bic_xml_tag': bic_xml_tag,
            'name_maxsize': name_maxsize,
            'convert_to_ascii': convert_to_ascii,
            'payment_method': 'DD',
            'pain_flavor': pain_flavor,
            'sepa_export': sepa_export,
            'file_obj': self.pool['banking.export.sdd'],
            'pain_xsd_file': '%s/data/%s.xsd' % (module, pain_flavor)
        }

        pain_ns = {
            'xs': 'http://www.w3.org/2001/XMLSchema-instance',
            None: 'http://www.six-interbank-clearing.com/de/%s.xsd'
                  % pain_flavor,
        }

        xml_root = etree.Element('Document', nsmap=pain_ns)
        pain_root = etree.SubElement(xml_root, root_xml_tag)

        # A. Group header
        group_header_1_0, nb_of_transactions_1_6, control_sum_1_7 = \
            self.generate_group_header_block(
                cr, uid, pain_root, gen_args, context=context)

        transactions_count_1_6 = 0
        total_amount = 0.0
        amount_control_sum_1_7 = 0.0
        lines_per_group = {}
        # key = (requested_date, priority, sequence type)
        # value = list of lines as objects
        # Iterate on payment orders
        today = fields.date.context_today(self, cr, uid, context=context)
        for payment_order in sepa_export.payment_order_ids:
            total_amount = total_amount + payment_order.total
            # Iterate each payment lines
            for line in payment_order.line_ids:
                transactions_count_1_6 += 1
                priority = line.priority
                if payment_order.date_prefered == 'due':
                    requested_date = line.ml_maturity_date or today
                elif payment_order.date_prefered == 'fixed':
                    requested_date = payment_order.date_scheduled or today
                else:
                    requested_date = today
                if not line.mandate_id:
                    raise orm.except_orm(
                        _('Error:'),
                        _("Missing SEPA Direct Debit mandate on the payment "
                          "line with partner '%s' and Invoice ref '%s'.")
                        % (line.partner_id.name,
                           line.ml_inv_ref.number))
                scheme = line.mandate_id.scheme
                if line.mandate_id.state != 'valid':
                    raise orm.except_orm(
                        _('Error:'),
                        _("The SEPA Direct Debit mandate with reference '%s' "
                          "for partner '%s' has expired.")
                        % (line.mandate_id.unique_mandate_reference,
                           line.mandate_id.partner_id.name))
                if line.mandate_id.type == 'oneoff':
                    if not line.mandate_id.last_debit_date:
                        seq_type = 'OOFF'
                    else:
                        raise orm.except_orm(
                            _('Error:'),
                            _("The mandate with reference '%s' for partner "
                              "'%s' has type set to 'One-Off' and it has a "
                              "last debit date set to '%s', so we can't use "
                              "it.")
                            % (line.mandate_id.unique_mandate_reference,
                               line.mandate_id.partner_id.name,
                               line.mandate_id.last_debit_date))
                elif line.mandate_id.type == 'recurrent':
                    seq_type_map = {
                        'recurring': 'RCUR',
                        'first': 'FRST',
                        'final': 'FNAL',
                    }
                    seq_type_label = \
                        line.mandate_id.recurrent_sequence_type
                    assert seq_type_label is not False
                    seq_type = seq_type_map[seq_type_label]

                key = (requested_date, priority, seq_type, scheme)
                if key in lines_per_group:
                    lines_per_group[key].append(line)
                else:
                    lines_per_group[key] = [line]
                # Write requested_exec_date on 'Payment date' of the pay line
                if requested_date != line.date:
                    self.pool['payment.line'].write(
                        cr, uid, line.id,
                        {'date': requested_date}, context=context)

        for (requested_date, priority, sequence_type, scheme), lines in \
                lines_per_group.items():
            # B. Payment info
            payment_info_2_0, nb_of_transactions_2_4, control_sum_2_5 = \
                self.generate_start_payment_info_block(
                    cr, uid, pain_root,
                    "sepa_export.payment_order_ids[0].reference + '-' + "
                    "sequence_type + '-' + requested_date.replace('-', '')  "
                    "+ '-' + priority",
                    False, scheme, sequence_type, requested_date, {
                        'sepa_export': sepa_export,
                        'sequence_type': sequence_type,
                        'priority': priority,
                        'requested_date': requested_date,
                    }, gen_args, context=context)

            self.generate_party_block(
                cr, uid, payment_info_2_0, 'Cdtr', 'B',
                'sepa_export.payment_order_ids[0].mode.bank_id.partner_id.'
                'name',
                'sepa_export.payment_order_ids[0].mode.bank_id.acc_number',
                'sepa_export.payment_order_ids[0].mode.bank_id.bank.bic',
                {'sepa_export': sepa_export},
                gen_args, context=context)

            charge_bearer_2_24 = etree.SubElement(payment_info_2_0, 'ChrgBr')
            charge_bearer_2_24.text = sepa_export.charge_bearer

            creditor_scheme_identification_2_27 = etree.SubElement(
                payment_info_2_0, 'CdtrSchmeId')
            self.generate_creditor_scheme_identification(
                cr, uid, creditor_scheme_identification_2_27,
                'sepa_export.payment_order_ids[0].company_id.'
                'sepa_creditor_identifier',
                'SEPA Creditor Identifier', {'sepa_export': sepa_export},
                'SEPA', gen_args, context=context)

            transactions_count_2_4 = 0
            amount_control_sum_2_5 = 0.0
            for line in lines:
                transactions_count_2_4 += 1
                # C. Direct Debit Transaction Info
                dd_transaction_info_2_28 = etree.SubElement(
                    payment_info_2_0, 'DrctDbtTxInf')
                payment_identification_2_29 = etree.SubElement(
                    dd_transaction_info_2_28, 'PmtId')
                if pain_flavor == 'pain.008.001.02.ch.01':
                    instruction_identification = etree.SubElement(
                        payment_identification_2_29, 'InstrId')
                    instruction_identification.text = self._prepare_field(
                        cr, uid, 'Intruction Identification', 'line.name',
                        {'line': line}, 35, gen_args=gen_args, context=context)
                end2end_identification_2_31 = etree.SubElement(
                    payment_identification_2_29, 'EndToEndId')
                end2end_identification_2_31.text = self._prepare_field(
                    cr, uid, 'End to End Identification', 'line.name',
                    {'line': line}, 35,
                    gen_args=gen_args, context=context)
                currency_name = self._prepare_field(
                    cr, uid, 'Currency Code', 'line.currency.name',
                    {'line': line}, 3, gen_args=gen_args,
                    context=context)
                instructed_amount_2_44 = etree.SubElement(
                    dd_transaction_info_2_28, 'InstdAmt', Ccy=currency_name)
                instructed_amount_2_44.text = '%.2f' % line.amount_currency
                amount_control_sum_1_7 += line.amount_currency
                amount_control_sum_2_5 += line.amount_currency
                dd_transaction_2_46 = etree.SubElement(
                    dd_transaction_info_2_28, 'DrctDbtTx')
                mandate_related_info_2_47 = etree.SubElement(
                    dd_transaction_2_46, 'MndtRltdInf')
                mandate_identification_2_48 = etree.SubElement(
                    mandate_related_info_2_47, 'MndtId')
                mandate_identification_2_48.text = self._prepare_field(
                    cr, uid, 'Unique Mandate Reference',
                    'line.mandate_id.unique_mandate_reference',
                    {'line': line}, 35,
                    gen_args=gen_args, context=context)
                mandate_signature_date_2_49 = etree.SubElement(
                    mandate_related_info_2_47, 'DtOfSgntr')
                mandate_signature_date_2_49.text = self._prepare_field(
                    cr, uid, 'Mandate Signature Date',
                    'line.mandate_id.signature_date',
                    {'line': line}, 10,
                    gen_args=gen_args, context=context)
                if sequence_type == 'FRST' and (
                    line.mandate_id.last_debit_date or not
                        line.mandate_id.sepa_migrated):
                    previous_bank = self._get_previous_bank(
                        cr, uid, line, context=context)
                    if previous_bank or not line.mandate_id.sepa_migrated:
                        amendment_indicator_2_50 = etree.SubElement(
                            mandate_related_info_2_47, 'AmdmntInd')
                        amendment_indicator_2_50.text = 'true'
                        amendment_info_details_2_51 = etree.SubElement(
                            mandate_related_info_2_47, 'AmdmntInfDtls')
                    if previous_bank:
                        if previous_bank.bank.bic == line.bank_id.bank.bic:
                            ori_debtor_account_2_57 = etree.SubElement(
                                amendment_info_details_2_51, 'OrgnlDbtrAcct')
                            ori_debtor_account_id = etree.SubElement(
                                ori_debtor_account_2_57, 'Id')
                            ori_debtor_account_iban = etree.SubElement(
                                ori_debtor_account_id, 'IBAN')
                            ori_debtor_account_iban.text = self._validate_iban(
                                cr, uid, self._prepare_field(
                                    cr, uid, 'Original Debtor Account',
                                    'previous_bank.acc_number',
                                    {'previous_bank': previous_bank},
                                    gen_args=gen_args,
                                    context=context),
                                context=context)
                        else:
                            ori_debtor_agent_2_58 = etree.SubElement(
                                amendment_info_details_2_51, 'OrgnlDbtrAgt')
                            ori_debtor_agent_institution = etree.SubElement(
                                ori_debtor_agent_2_58, 'FinInstnId')
                            ori_debtor_agent_bic = etree.SubElement(
                                ori_debtor_agent_institution, bic_xml_tag)
                            ori_debtor_agent_bic.text = self._prepare_field(
                                cr, uid, 'Original Debtor Agent',
                                'previous_bank.bank.bic',
                                {'previous_bank': previous_bank},
                                gen_args=gen_args,
                                context=context)
                            ori_debtor_agent_other = etree.SubElement(
                                ori_debtor_agent_institution, 'Othr')
                            ori_debtor_agent_other_id = etree.SubElement(
                                ori_debtor_agent_other, 'Id')
                            ori_debtor_agent_other_id.text = 'SMNDA'
                            # SMNDA = Same Mandate New Debtor Agent
                    elif not line.mandate_id.sepa_migrated:
                        ori_mandate_identification_2_52 = etree.SubElement(
                            amendment_info_details_2_51, 'OrgnlMndtId')
                        ori_mandate_identification_2_52.text = \
                            self._prepare_field(
                                cr, uid, 'Original Mandate Identification',
                                'line.mandate_id.'
                                'original_mandate_identification',
                                {'line': line},
                                gen_args=gen_args,
                                context=context)
                        ori_creditor_scheme_id_2_53 = etree.SubElement(
                            amendment_info_details_2_51, 'OrgnlCdtrSchmeId')
                        self.generate_creditor_scheme_identification(
                            cr, uid, ori_creditor_scheme_id_2_53,
                            'sepa_export.payment_order_ids[0].company_id.'
                            'original_creditor_identifier',
                            'Original Creditor Identifier',
                            {'sepa_export': sepa_export},
                            'SEPA', gen_args, context=context)

                self.generate_party_block(
                    cr, uid, dd_transaction_info_2_28, 'Dbtr', 'C',
                    'line.partner_id.name',
                    'line.bank_id.acc_number',
                    'line.bank_id.bank.bic',
                    {'line': line}, gen_args, context=context)

                self.generate_remittance_info_block(
                    cr, uid, dd_transaction_info_2_28,
                    line, gen_args, context=context)

            nb_of_transactions_2_4.text = str(transactions_count_2_4)
            control_sum_2_5.text = '%.2f' % amount_control_sum_2_5
        nb_of_transactions_1_6.text = str(transactions_count_1_6)
        control_sum_1_7.text = '%.2f' % amount_control_sum_1_7

        return self.finalize_sepa_file_creation(
            cr, uid, ids, xml_root, total_amount, transactions_count_1_6,
            gen_args, context=context)
