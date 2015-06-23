##############################################################################
#
#    Swiss localization Direct Debit module for OpenERP
#    Copyright (C) 2014 Compassion (http://www.compassion.ch)
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

import base64
import collections
from datetime import date, datetime, timedelta
from openerp import netsvc
from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools import mod10r
from openerp.tools.translate import _

import logging
logger = logging.getLogger(__name__)


class post_dd_export_wizard(orm.TransientModel):

    ''' Postfinance Direct Debit file generation wizard.
        This wizard is called when the "make payment" button on a
        direct debit order with payment type "Postfinance DD" is pressed.
    '''
    _name = 'post.dd.export.wizard'
    _description = 'Export Postfinance Direct Debit File'

    _columns = {
        'currency': fields.selection([
            ('CHF', 'CHF'),
            ('EUR', 'EUR')], _('Currency'), required=True),
        'banking_export_ch_dd_id': fields.many2one(
            'banking.export.ch.dd', _('Direct Debit file'), readonly=True),
        'file': fields.related(
            'banking_export_ch_dd_id', 'file', string=_('File'),
            type='binary', readonly=True),
        'filename': fields.related(
            'banking_export_ch_dd_id', 'filename', string=_('Filename'),
            type='char', size=256, readonly=True),
        'nb_transactions': fields.related(
            'banking_export_ch_dd_id', 'nb_transactions', type='integer',
            string=_('Number of Transactions'), readonly=True),
        'total_amount': fields.related(
            'banking_export_ch_dd_id', 'total_amount', type='float',
            string=_('Total Amount'), readonly=True),
        'state': fields.selection([
            ('create', _('Create')),
            ('finish', _('Finish'))], _('State'), readonly=True),
    }

    _defaults = {
        'currency': 'CHF',
        'state': 'create',
    }

    def generate_dd_file(self, cr, uid, ids, context=None):
        ''' Generate direct debit export object including the direct
            debit file content.
            Called by generate button
        '''
        payment_order_obj = self.pool.get('payment.order')
        payment_line_obj = self.pool.get('payment.line')

        active_ids = context.get('active_ids', [])
        if not active_ids:
            raise orm.except_orm('ValueError', _('No payment order selected'))
        payment_order_ids = payment_order_obj.browse(cr, uid,
                                                     active_ids, context)

        properties = self._setup_properties(cr, uid, context, ids[0],
                                            payment_order_ids[0])

        records = []
        overall_amount = 0

        for payment_order in payment_order_ids:
            overall_amount += payment_order.total
            # Order payment_lines to simplify the setup of 'group orders'
            order_by = ''
            if payment_order.date_prefered == 'due':
                order_by = 'account_move_line.date_maturity ASC, '
            order_by += 'payment_line.bank_id'

            # A direct db query is used because order parameter in
            # model.search doesn't work over function fields
            cr.execute(
                'SELECT payment_line.id '
                'FROM payment_line, account_move_line '
                'WHERE payment_line.move_line_id = account_move_line.id '
                'AND payment_line.order_id = %s '
                'ORDER BY ' + order_by, (payment_order.id,))
            sorted_line_ids = [row[0] for row in cr.fetchall()]
            payment_lines = payment_line_obj.browse(cr, uid, sorted_line_ids,
                                                    context)

            if not payment_lines:
                continue

            # Setup dates for grouping comparison and head_record generation
            previous_date = payment_lines[0].ml_maturity_date
            order_date = self._get_treatment_date(
                payment_order.date_prefered, payment_lines[0].ml_maturity_date,
                payment_order.date_scheduled, payment_lines[0].name)
            properties.update({'due_date': self._prepare_date(order_date),
                               'trans_ser_no': 0})

            total_amount = 0.0
            # Records is a list of tuples (payment_line, generated line).
            # This is to help customization. Head and total row have no
            # associated payment_line
            records.append((None, self._generate_head_record(properties)))
            properties.update({'trans_ser_no': properties['trans_ser_no'] + 1})
            for line in payment_lines:
                if not line.mandate_id or not line.mandate_id.state == "valid":
                    raise orm.except_orm(
                        'ValueError',
                        _('Line with ref %s has no associated valid mandate') %
                        line.name)

                if (payment_order.date_prefered == 'due' and
                        not previous_date == line.ml_maturity_date):
                    records.append((None,
                                    self._generate_total_record(
                                        properties, total_amount)))
                    total_amount = 0.0
                    due_date = self._get_treatment_date(
                        payment_order.date_prefered,
                        line.ml_maturity_date,
                        payment_order.date_scheduled,
                        line.name)
                    properties.update({
                        'dd_order_no': properties['dd_order_no'] + 1,
                        'trans_ser_no': 0,
                        'due_date': self._prepare_date(due_date)})
                    records.append(
                        (None, self._generate_head_record(properties)))
                    properties.update(
                        {'trans_ser_no': properties['trans_ser_no'] + 1})
                    previous_date = line.ml_maturity_date

                records.append((line, self._generate_debit_record(
                    line, properties, payment_order, cr, uid, context)))
                properties.update(
                    {'nb_transactions': properties.get('nb_transactions') + 1})
                total_amount = total_amount + line.amount_currency
                properties.update(
                    {'trans_ser_no': properties['trans_ser_no'] + 1})

            records.append((None, self._generate_total_record(properties,
                                                              total_amount)))
            properties.update({'dd_order_no': properties['dd_order_no'] + 1})

        records = self._customize_records(cr, uid, records, properties,
                                          context)
        file_content = ''.join(records)  # Concatenate all records
        file_content = file_content.encode('iso8859-1')  # Required encoding

        export_id = self._create_dd_export(cr, uid, context, active_ids,
                                           overall_amount, properties,
                                           file_content)
        self.write(cr, uid, ids, {'banking_export_ch_dd_id': export_id,
                                  'state': 'finish'}, context=context)

        action = {
            'name': 'Generated File',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': self._name,
            'res_id': ids[0],
            'target': 'new',
        }
        return action

    def _generate_head_record(self, properties):
        ''' Head record generation (Transaction type 00) '''
        control_range = self._gen_control_range('00', properties)
        head_record = control_range + self._complete_line('', 650)

        if len(head_record) == 700:  # Standard head record size
            return head_record
        else:
            raise orm.except_orm(
                'RuntimeError',
                _('Generated head record with size %d is not valid '
                  '(len should be 700)') % len(head_record))

    def _generate_debit_record(self, line, properties, payment_order,
                               cr, uid, context):
        ''' Convert each payment_line to postfinance debit record
            (Transaction type 47)
        '''
        control_range = self._gen_control_range('47', properties)

        vals = collections.OrderedDict()
        self._check_currency(line, properties)
        vals['currency'] = properties.get('currency', 'CHF')
        self._check_amount(line, properties)
        vals['amount'] = self._format_number(line.amount_currency, 13)
        vals['reserve_1'] = self._complete_line('', 1)
        vals['reserve_2'] = self._complete_line('', 3)
        vals['reserve_3'] = self._complete_line('', 2)
        vals['deb_account_no'] = self._get_post_account(line.bank_id)
        vals['reserve_4'] = self._complete_line('', 6)
        vals['ref'] = self._complete_line(self._get_ref(cr, uid, context,
                                                        line), 27)
        vals['reserve_5'] = self._complete_line('', 8)
        vals['deb_address'] = self._get_account_address(line.bank_id)
        vals['reserve_6'] = self._complete_line('', 35)
        vals['reserve_7'] = self._complete_line('', 35)
        vals['reserve_8'] = self._complete_line('', 35)
        vals['reserve_9'] = self._complete_line('', 10)
        vals['reserve_10'] = self._complete_line('', 25)
        communications = self._get_communications(cr, uid, line, context)
        vals['communication'] = self._complete_line(communications, 140)
        vals['reserve_11'] = self._complete_line('', 3)
        vals['reserve_12'] = self._complete_line('', 1)
        vals['orderer_info'] = self._complete_line('', 140)  # Not implemented
        vals['reserve_13'] = self._complete_line('', 14)

        debit_record = control_range + ''.join(vals.values())

        if len(debit_record) == 700:  # Standard debit record size
            return debit_record
        else:
            raise orm.except_orm(
                'RuntimeError',
                _('Generated debit_record with size %d is not valid '
                  '(len should be 700)') % len(debit_record))

    def _generate_total_record(self, properties, total_amount):
        ''' Generate total line according to total amount and properties
            (Transaction type 97)
        '''
        control_range = self._gen_control_range('97', properties)

        vals = collections.OrderedDict()
        vals['currency'] = properties.get('currency', 'CHF')
        vals['nb_transactions'] = str(
            properties.get('trans_ser_no') -
            1).zfill(6)
        vals['total_amount'] = self._format_number(total_amount, 13)
        vals['reserve_1'] = self._complete_line('', 628)

        total_record = control_range + ''.join(vals.values())
        if len(total_record) == 700:
            return total_record
        else:
            raise orm.except_orm(
                'RuntimeError',
                _('Generated total line is not valid (%d instead of 700)') %
                len(total_record))

    def _create_dd_export(self, cr, uid, context, p_o_ids, total_amount,
                          properties, file_content):
        ''' Create banking.export.ch.dd object '''
        banking_export_ch_dd_obj = self.pool.get('banking.export.ch.dd')
        vals = {
            'payment_order_ids': [(6, 0, [p_o_id for p_o_id in p_o_ids])],
            'total_amount': total_amount,
            'nb_transactions': properties.get('nb_transactions'),
            'file': base64.encodestring(file_content),
            'type': 'Postfinance Direct Debit',
        }
        export_id = banking_export_ch_dd_obj.create(cr, uid, vals,
                                                    context=context)
        return export_id

    def confirm_export(self, cr, uid, ids, context=None):
        ''' Save the exported DD file: mark all payments in the file
            as 'sent'. Write 'last debit date' on mandate.
        '''
        export_wizard = self.browse(cr, uid, ids[0], context=context)
        self.pool.get('banking.export.ch.dd').write(
            cr, uid, export_wizard.banking_export_ch_dd_id.id, {
                'state': 'sent'}, context=context)
        wf_service = netsvc.LocalService('workflow')
        today_str = datetime.today().strftime(DF)
        for order in export_wizard.banking_export_ch_dd_id.payment_order_ids:
            wf_service.trg_validate(uid, 'payment.order', order.id, 'done', cr)
            mandate_ids = [line.mandate_id.id for line in order.line_ids]
            self.pool['account.banking.mandate'].write(
                cr, uid, mandate_ids, {
                    'last_debit_date': today_str}, context=context)

        # redirect to generated dd export
        action = {
            'name': 'Generated File',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'banking.export.ch.dd',
            'res_id': export_wizard.banking_export_ch_dd_id.id,
            'target': 'current',
        }
        return action

    def cancel_export(self, cr, uid, ids, context=None):
        ''' Cancel the export: delete export record '''
        export_wizard = self.browse(cr, uid, ids[0], context=context)
        self.pool.get('banking.export.ch.dd').unlink(
            cr, uid, export_wizard.banking_export_ch_dd_id.id, context=context)
        return {'type': 'ir.actions.act_window_close'}

    def _customize_records(self, cr, uid, records, properties, context=None):
        ''' Use this function if you want to customize the generated lines.
            @param records: list of tuples with tup[0]=payment line and
                              tup[1]=generated string.
            @return: list of strings.
        '''
        return [tup[1] for tup in records]

    ##########################
    #         Tools          #
    ##########################
    def _check_amount(self, line, properties):
        ''' Max allowed amount is CHF 10'000'000.00 and EUR 5'000'000.00 '''
        if (properties.get('currency') == 'CHF' and
                line.amount_currency > 10000000.00) or (
                    properties.get('currency') == 'EUR' and
                    line.amount_currency > 5000000.00):
            raise orm.except_orm(
                'ValueError',
                _('Max authorized amount is CHF 10\'000\'000.00 '
                  'or EUR 5\'000\'000.00 (%s %.2f given for ref %s)') %
                (properties.get('currency'), line.amount_currency, line.name))
        elif line.amount_currency <= 0:
            raise orm.except_orm(
                'ValueError',
                _('Amount for line with ref %s is negative (%f '
                  'given)') % (line.name, line.amount_currency))

    def _check_currency(self, line, properties):
        ''' Check that line currency is equal to dd export currency '''
        if not line.currency.name == properties.get('currency'):
            raise orm.except_orm(
                'ValueError',
                _('Line with ref %s has %s currency and direct '
                  'debit file %s (should be the same)') %
                (line.name, line.currency.name, properties.get(
                    'currency', '')))

    def _complete_line(self, string, nb_char):
        ''' In DD file each field has a defined length.
            This way, lines have to be filled with spaces (or truncated).
        '''
        if len(string) > nb_char:
            return string[:nb_char]

        return string.ljust(nb_char)

    def _format_number(self, amount, nb_char):
        ''' Accepted format is "0000000012350" for "123.50" '''
        amount_str = '{:.2f}'.format(amount).replace('.', '').zfill(nb_char)
        return amount_str

    def _gen_control_range(self, trans_type, properties):
        vals = collections.OrderedDict()
        vals['file_id'] = '036'
        vals['due_date'] = properties.get('due_date')
        vals['dd_customer_no'] = properties.get('dd_customer_no')
        vals['control_attr'] = '1'
        vals['reserve_1'] = ''.zfill(8)  # In 2 lines like in spec...
        vals['reserve_2'] = ''.zfill(9)
        vals['dd_order_no'] = str(properties.get('dd_order_no')).zfill(2)
        vals['trans_type'] = trans_type.zfill(2)
        vals['trans_serial_no'] = str(properties.get('trans_ser_no')).zfill(6)
        vals['reserve_3'] = ''.zfill(2)
        vals['reserve_4'] = ''.zfill(1)
        vals['reserve_5'] = ''.zfill(4)

        return ''.join(vals.values())

    def _get_account_address(self, bank_account):
        ''' Return account address for given bank_account.
            First line is mandatory !
        '''
        if bank_account.owner_name:
            line1_owner = bank_account.owner_name
        else:
            raise orm.except_orm('ValueError',
                                 _('Missing owner name for bank account %s')
                                 % bank_account.acc_number)

        line2_owner_cmpl = ''
        line3_address = bank_account.street if bank_account.street else ''
        line4_zip = bank_account.zip if bank_account.zip else ''
        line5_city = bank_account.city if bank_account.city else ''

        return (self._complete_line(line1_owner, 35) +
                self._complete_line(line2_owner_cmpl, 35) +
                self._complete_line(line3_address, 35) +
                self._complete_line(line4_zip, 10) +
                self._complete_line(line5_city, 25))

    def _get_post_account(self, bank_account):
        ''' Returns BV/BVR account in format 123456789 rather than
            12-345678-9
        '''
        clean_account = bank_account.acc_number.replace(' ', '').replace(
            '-', '')
        if len(clean_account) < 9:
            clean_account = clean_account[
                0:2] + ''.zfill(9 - len(clean_account)) + clean_account[2:]
        elif len(clean_account) > 9:
            raise orm.except_orm(
                'ValueError',
                _('Given BV account number is to long ! (%s)') %
                clean_account)
        return clean_account

    def _get_communications(self, cr, uid, line, context=None):
        ''' This method can be overloaded to fit your communication style '''
        return ''

    def _get_ref(self, cr, uid, context, payment_line):
        if self._is_bvr_ref(cr, uid,
                            payment_line.move_line_id.transaction_ref):
            return payment_line.move_line_id.transaction_ref.replace(
                ' ', '').rjust(27, '0')
        else:
            return ''

    def _is_bvr_ref(self, cr, uid, ref, context=None):
        if not ref:
            return False  # Empty is not valid
        clean_ref = ref.replace(' ', '')
        if not clean_ref.isdigit() or len(clean_ref) > 27:
            return False
        clean_ref = clean_ref.rjust(27, '0')  # Add zeros to the left
        if not clean_ref == mod10r(clean_ref[0:26]):
            return False

        return True

    def _get_treatment_date(self, prefered_type, line_mat_date,
                            order_sched_date, name):
        ''' Returns appropriate date according to payment_order and
            payment_order_line data.
            Raises an error if treatment date is > today+30 or < today-10
        '''
        requested_date = date.today()
        if prefered_type == 'due':
            requested_date = datetime.strptime(line_mat_date, DF).date() \
                or requested_date
        elif prefered_type == 'fixed':
            requested_date = datetime.strptime(order_sched_date, DF).date() \
                or requested_date

        # Accepted dates are in range -90 to +90 days. We could go up
        # to +1 year, but we should be sure that we have less than
        # 1000 lines in payment order
        if requested_date > date.today() + timedelta(days=90) \
                or requested_date < date.today() - timedelta(days=90):
            raise orm.except_orm(
                'ValueError',
                _('Incorrect treatment date: %s for line with '
                  'ref %s') % (requested_date, name))

        return requested_date

    def _prepare_date(self, format_date):
        ''' Returns date formatted to YYMMDD string '''
        return format_date.strftime('%y%m%d')

    def _setup_properties(self, cr, uid, context, wizard_id, payment_order):
        ''' These properties are the same for all lines of the DD file '''
        form = self.browse(cr, uid, wizard_id, context)
        if not payment_order.mode.bank_id.post_dd_identifier:
            raise orm.except_orm(
                'RuntimeError',
                _('Missing Postfinance direct debit identifier for account '
                  '%s') % payment_order.mode.bank_id.acc_number)

        properties = {
            'dd_customer_no': payment_order.mode.bank_id.post_dd_identifier,
            'dd_order_no': 1,
            'trans_ser_no': 0,
            'nb_transactions': 0,
            'currency': form.currency,
        }

        return properties
