# -*- coding: utf-8 -*-
##############################################################################
#
#    SEPA Credit Transfer module for OpenERP
#    Copyright (C) 2010-2013 Akretion (http://www.akretion.com)
#    @author: Alexis de Lattre <alexis.delattre@akretion.com>
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
    _inherit = 'banking.export.sepa.wizard'

    def generate_party_agent(
            self, cr, uid, parent_node, party_type, party_type_label,
            order, party_name, iban, bic, eval_ctx, gen_args, context=None):
        '''Generate the piece of the XML file corresponding to BIC
        This code is mutualized between TRF and DD'''
        assert order in ('B', 'C'), "Order can be 'B' or 'C'"
        party_agent = etree.SubElement(parent_node, '%sAgt' % party_type)
        party_agent_institution = etree.SubElement(
            party_agent, 'FinInstnId')
        if order == 'C' and eval_ctx['line'].local_instrument == 'CH03':
            if not eval_ctx['line'].bank_id.bank.clearing:
                raise orm.except_orm(
                    _('Error:'),
                    _("The bank account with IBAN '%s' of partner '%s' must "
                      "have correct clearing for "
                      "payment type pain 2.2 'CH03'")
                    % (iban, party_name))
            clearing_system_memb = etree.SubElement(
                party_agent_institution, 'ClrSysMmbId')
            clearing_system_id = etree.SubElement(
                clearing_system_memb, 'ClrSysId')
            clearing_system_id_code = etree.SubElement(
                clearing_system_id, 'Cd')
            clearing_system_id_code.text = "CHBCC"
            clearing_member_id = etree.SubElement(
                clearing_system_memb, "MmbId")
            clearing_member_id.text = eval_ctx['line'].bank_id.bank.clearing
        else:
            try:
                bic = self._prepare_field(
                    cr, uid, '%s BIC' % party_type_label, bic, eval_ctx,
                    gen_args=gen_args, context=context)

                party_agent_bic = etree.SubElement(
                    party_agent_institution, gen_args.get('bic_xml_tag'))
                party_agent_bic.text = bic
            except orm.except_orm:
                if order == 'C':
                    if iban[0:2] != gen_args['initiating_party_country_code']:
                        raise orm.except_orm(
                            _('Error:'),
                            _("The bank account with IBAN '%s' of '%s' "
                              "partner must have an associated BIC "
                              "because it is a cross-border SEPA operation.")
                            % (iban, party_name))
                if order == 'B' or (
                        order == 'C' and gen_args['payment_method'] == 'DD'):
                    party_agent_other = etree.SubElement(
                        party_agent_institution, 'Othr')
                    party_agent_other_identification = etree.SubElement(
                        party_agent_other, 'Id')
                    party_agent_other_identification.text = 'NOTPROVIDED'
                # for Credit Transfers, in the 'C' block,
                # if BIC is not provided,
                # we should not put the 'Creditor Agent' block at all,
                # as per the guidelines of the EPC
            return True

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
            if not eval_ctx['line'].local_instrument in ["CH01", "CH02"]:
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

    def generate_start_payment_info_block(
            self, cr, uid, parent_node, payment_info_ident,
            priority, local_instrument, sequence_type, requested_date,
            eval_ctx, gen_args, context=None):
        payment_info_2_0 = etree.SubElement(parent_node, 'PmtInf')
        payment_info_identification_2_1 = etree.SubElement(
            payment_info_2_0, 'PmtInfId')
        payment_info_identification_2_1.text = self._prepare_field(
            cr, uid, 'Payment Information Identification',
            payment_info_ident, eval_ctx, 35,
            gen_args=gen_args, context=context)
        payment_method_2_2 = etree.SubElement(payment_info_2_0, 'PmtMtd')
        payment_method_2_2.text = gen_args['payment_method']
        if gen_args.get('pain_flavor') != 'pain.001.001.02':
            batch_booking_2_3 = etree.SubElement(payment_info_2_0, 'BtchBookg')
            batch_booking_2_3.text = \
                str(gen_args['sepa_export'].batch_booking).lower()
        # The "SEPA Customer-to-bank
        # Implementation guidelines" for SCT and SDD says that control sum
        # and nb_of_transactions should be present
        # at both "group header" level and "payment info" level
            nb_of_transactions_2_4 = etree.SubElement(
                payment_info_2_0, 'NbOfTxs')
            control_sum_2_5 = etree.SubElement(payment_info_2_0, 'CtrlSum')
        payment_type_info_2_6 = etree.SubElement(
            payment_info_2_0, 'PmtTpInf')
        if eval_ctx['sepa_export'].charge_bearer == "SLEV":
            if local_instrument:
                raise orm.except_orm(
                    _('Error:'),
                    _("SLEV is for SEPA payments, not for local."
                      "one of lines in order have local instrument specified"))
            if priority:
                instruction_priority_2_7 = etree.SubElement(
                    payment_type_info_2_6, 'InstrPrty')
                instruction_priority_2_7.text = priority
            service_level_2_8 = etree.SubElement(
                payment_type_info_2_6, 'SvcLvl')
            service_level_code_2_9 = etree.SubElement(service_level_2_8, 'Cd')
            service_level_code_2_9.text = 'SEPA'
        if local_instrument:
            local_instrument_2_11 = etree.SubElement(
                payment_type_info_2_6, 'LclInstrm')
            local_instr_code_2_12 = etree.SubElement(
                local_instrument_2_11, 'Prtry')
            local_instr_code_2_12.text = local_instrument
        if sequence_type:
            sequence_type_2_14 = etree.SubElement(
                payment_type_info_2_6, 'SeqTp')
            sequence_type_2_14.text = sequence_type

        if gen_args['payment_method'] == 'DD':
            request_date_tag = 'ReqdColltnDt'
        else:
            request_date_tag = 'ReqdExctnDt'
        requested_date_2_17 = etree.SubElement(
            payment_info_2_0, request_date_tag)
        requested_date_2_17.text = requested_date
        return payment_info_2_0, nb_of_transactions_2_4, control_sum_2_5

    def create_sepa(self, cr, uid, ids, context=None):
        '''
        Creates the SEPA Credit Transfer file. That's the important code !
        '''
        if context is None:
            context = {}
        sepa_export = self.browse(cr, uid, ids[0], context=context)
        pain_flavor = sepa_export.payment_order_ids[0].mode.type.code
        convert_to_ascii = \
            sepa_export.payment_order_ids[0].mode.convert_to_ascii
        if pain_flavor == 'pain.001.001.02':
            bic_xml_tag = 'BIC'
            name_maxsize = 70
            root_xml_tag = 'pain.001.001.02'
        elif pain_flavor == 'pain.001.001.03':
            bic_xml_tag = 'BIC'
            # size 70 -> 140 for <Nm> with pain.001.001.03
            # BUT the European Payment Council, in the document
            # "SEPA Credit Transfer Scheme Customer-to-bank
            # Implementation guidelines" v6.0 available on
            # http://www.europeanpaymentscouncil.eu/knowledge_bank.cfm
            # says that 'Nm' should be limited to 70
            # so we follow the "European Payment Council"
            # and we put 70 and not 140
            name_maxsize = 70
            root_xml_tag = 'CstmrCdtTrfInitn'
        elif pain_flavor == 'pain.001.001.04':
            bic_xml_tag = 'BICFI'
            name_maxsize = 140
            root_xml_tag = 'CstmrCdtTrfInitn'
        elif pain_flavor == 'pain.001.001.05':
            bic_xml_tag = 'BICFI'
            name_maxsize = 140
            root_xml_tag = 'CstmrCdtTrfInitn'
        # added pain.001.003.03 for German Banks
        # it is not in the offical ISO 20022 documentations, but nearly all
        # german banks are working with this instead 001.001.03
        elif pain_flavor == 'pain.001.003.03':
            bic_xml_tag = 'BIC'
            name_maxsize = 70
            root_xml_tag = 'CstmrCdtTrfInitn'
        elif pain_flavor == 'pain.001.001.03.ch.02':
            bic_xml_tag = 'BIC'
            name_maxsize = 70
            root_xml_tag = 'CstmrCdtTrfInitn'
        else:
            raise orm.except_orm(
                _('Error:'),
                _("Payment Type Code '%s' is not supported. The only "
                    "Payment Type Codes supported for SEPA Credit Transfers "
                    "are 'pain.001.001.02', 'pain.001.001.03', "
                    "'pain.001.001.04', 'pain.001.001.05',"
                    " 'pain.001.003.03' and 'pain.001.001.03.ch.02'.") %
                pain_flavor)

        if pain_flavor == 'pain.001.001.03.ch.02':
            module = 'l10n_ch_sepa_credit_transfer'

        else:
            module = 'account_banking_sepa_credit_transfer'
        gen_args = {
            'bic_xml_tag': bic_xml_tag,
            'name_maxsize': name_maxsize,
            'convert_to_ascii': convert_to_ascii,
            'payment_method': 'TRF',
            'pain_flavor': pain_flavor,
            'sepa_export': sepa_export,
            'file_obj': self.pool['banking.export.sepa'],
            'pain_xsd_file': '%s/data/%s.xsd' % (module, pain_flavor)
        }

        pain_ns = {
            'xs': 'http://www.w3.org/2001/XMLSchema-instance',
            None: 'http://www.six-interbank-clearing.com/de/%s.xsd'
                  % pain_flavor,
        }

        xml_root = etree.Element('Document', nsmap=pain_ns)
        pain_root = etree.SubElement(xml_root, root_xml_tag)
        pain_03_to_05 = [
            'pain.001.001.03',
            'pain.001.001.04',
            'pain.001.001.05',
            'pain.001.003.03'
        ]

        # A. Group header
        group_header_1_0, nb_of_transactions_1_6, control_sum_1_7 = \
            self.generate_group_header_block(
                cr, uid, pain_root, gen_args, context=context)

        transactions_count_1_6 = 0
        total_amount = 0.0
        amount_control_sum_1_7 = 0.0
        lines_per_group = {}
        # key = (requested_date, priority)
        # values = list of lines as object
        today = fields.date.context_today(self, cr, uid, context=context)
        for payment_order in sepa_export.payment_order_ids:
            total_amount = total_amount + payment_order.total
            for line in payment_order.line_ids:
                priority = line.priority
                local_instrument = line.local_instrument
                if payment_order.date_prefered == 'due':
                    requested_date = line.ml_maturity_date or today
                elif payment_order.date_prefered == 'fixed':
                    requested_date = payment_order.date_scheduled or today
                else:
                    requested_date = today
                key = (requested_date, priority, local_instrument)
                if key in lines_per_group:
                    lines_per_group[key].append(line)
                else:
                    lines_per_group[key] = [line]
                # Write requested_date on 'Payment date' of the pay line
                if requested_date != line.date:
                    self.pool['payment.line'].write(
                        cr, uid, line.id,
                        {'date': requested_date}, context=context)

        for (requested_date, priority,
             local_instrument), lines in lines_per_group.items():
            # B. Payment info
            payment_info_2_0, nb_of_transactions_2_4, control_sum_2_5 = \
                self.generate_start_payment_info_block(
                    cr, uid, pain_root,
                    "sepa_export.payment_order_ids[0].reference + '-' "
                    "+ requested_date.replace('-', '')  + '-' + priority",
                    priority, local_instrument, False, requested_date, {
                        'sepa_export': sepa_export,
                        'priority': priority,
                        'requested_date': requested_date,
                    }, gen_args, context=context)

            self.generate_party_block(
                cr, uid, payment_info_2_0, 'Dbtr', 'B',
                'sepa_export.payment_order_ids[0].mode.bank_id.partner_id.'
                'name',
                'sepa_export.payment_order_ids[0].mode.bank_id.acc_number',
                'sepa_export.payment_order_ids[0].mode.bank_id.bank.bic',
                {'sepa_export': sepa_export},
                gen_args, context=context)

            charge_bearer_2_24 = etree.SubElement(payment_info_2_0, 'ChrgBr')
            charge_bearer_2_24.text = sepa_export.charge_bearer

            transactions_count_2_4 = 0
            amount_control_sum_2_5 = 0.0
            for line in lines:
                transactions_count_1_6 += 1
                transactions_count_2_4 += 1
                # C. Credit Transfer Transaction Info
                credit_transfer_transaction_info_2_27 = etree.SubElement(
                    payment_info_2_0, 'CdtTrfTxInf')
                payment_identification_2_28 = etree.SubElement(
                    credit_transfer_transaction_info_2_27, 'PmtId')
                if pain_flavor == 'pain.001.001.03.ch.02':
                    instruction_identification_2_29 = etree.SubElement(
                        payment_identification_2_28, 'InstrId')
                    instruction_identification_2_29.text = self._prepare_field(
                        cr, uid, 'Intruction Identification', 'line.name',
                        {'line': line}, 35, gen_args=gen_args, context=context)
                end2end_identification_2_30 = etree.SubElement(
                    payment_identification_2_28, 'EndToEndId')
                end2end_identification_2_30.text = self._prepare_field(
                    cr, uid, 'End to End Identification', 'line.name',
                    {'line': line}, 35, gen_args=gen_args,
                    context=context)
                currency_name = self._prepare_field(
                    cr, uid, 'Currency Code', 'line.currency.name',
                    {'line': line}, 3, gen_args=gen_args,
                    context=context)
                amount_2_42 = etree.SubElement(
                    credit_transfer_transaction_info_2_27, 'Amt')
                instructed_amount_2_43 = etree.SubElement(
                    amount_2_42, 'InstdAmt', Ccy=currency_name)
                instructed_amount_2_43.text = '%.2f' % line.amount_currency
                amount_control_sum_1_7 += line.amount_currency
                amount_control_sum_2_5 += line.amount_currency

                if not line.bank_id:
                    raise orm.except_orm(
                        _('Error:'),
                        _("Missing Bank Account on invoice '%s' (payment "
                            "order line reference '%s').")
                        % (line.ml_inv_ref.number, line.name))
                self.generate_party_block(
                    cr, uid, credit_transfer_transaction_info_2_27, 'Cdtr',
                    'C', 'line.partner_id.name', 'line.bank_id.acc_number',
                    'line.bank_id.bank.bic', {'line': line}, gen_args,
                    context=context)

                self.generate_remittance_info_block(
                    cr, uid, credit_transfer_transaction_info_2_27,
                    line, gen_args, context=context)

            nb_of_transactions_2_4.text = str(transactions_count_2_4)
            control_sum_2_5.text = '%.2f' % amount_control_sum_2_5

        if pain_flavor in pain_03_to_05:
            nb_of_transactions_1_6.text = str(transactions_count_1_6)
            control_sum_1_7.text = '%.2f' % amount_control_sum_1_7
        else:
            nb_of_transactions_1_6.text = str(transactions_count_1_6)
            control_sum_1_7.text = '%.2f' % amount_control_sum_1_7

        return self.finalize_sepa_file_creation(
            cr, uid, ids, xml_root, total_amount, transactions_count_1_6,
            gen_args, context=context)
