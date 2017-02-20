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
from . import export_utils

from openerp import models, fields, api, _, exceptions

import logging
logger = logging.getLogger(__name__)


class PostDdExportWizard(models.TransientModel):

    ''' Postfinance Direct Debit file generation wizard.
        This wizard is called when the "make payment" button on a
        direct debit order with payment type "Postfinance DD" is pressed.

        In version 8, this wizard was called from the option in the More
        menu of a payment.order, but in version 9, to force the use of the
        workflow, we removed the entries in the menu. To avoid moving around
        the existing code, the wizard was kept (although now it can not
        be launched, but only instantiated to be used).
    '''
    _name = 'post.dd.export.wizard'
    _description = 'Export Postfinance Direct Debit File'

    currency = fields.Selection(
        [('CHF', 'CHF'),
         ('EUR', 'EUR'),
         ],
        required=True,
        default='CHF'
    )
    banking_export_ch_dd_id = fields.Many2one(
        'banking.export.ch.dd',
        'Direct Debit file',
        readonly=True
    )
    file = fields.Binary(
        related='banking_export_ch_dd_id.file'
    )
    filename = fields.Char(
        related='banking_export_ch_dd_id.filename',
        size=256,
        readonly=True
    )
    nb_transactions = fields.Integer(
        'Number of Transactions',
        related='banking_export_ch_dd_id.nb_transactions',
        readonly=True
    )
    total_amount = fields.Float(
        'Total Amount',
        related='banking_export_ch_dd_id.total_amount',
        readonly=True
    )
    state = fields.Selection(
        [('create', _('Create')), ('finish', _('Finish'))],
        readonly=True,
        default='create'
    )

    @api.multi
    def generate_dd_file(self):
        ''' Generate direct debit export object including the direct
            debit file content.
            Called by generate button
        '''
        self.ensure_one()
        payment_order_obj = self.env['account.payment.order']

        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            raise exceptions.ValidationError(_('No payment order selected'))

        payment_orders = payment_order_obj.browse(active_ids)
        properties = self._setup_properties(payment_orders[0])
        records = []
        overall_amount = 0

        for payment_order in payment_orders:
            overall_amount += payment_order.total_company_currency
            if not payment_order.payment_line_ids:
                continue

            # Order payment_lines to simplify the setup of 'group orders'
            payment_lines = payment_order.payment_line_ids.sorted(
                lambda pl: pl.partner_bank_id.id)
            if payment_order.date_prefered == 'due':
                payment_lines = payment_lines.sorted(
                    lambda pl: pl.move_line_id.date_maturity)

            # Setup dates for grouping comparison and head_record generation
            previous_date = payment_lines[0].ml_maturity_date
            order_date = export_utils.get_treatment_date(
                payment_order.date_prefered,
                payment_lines[0].ml_maturity_date,
                payment_order.date_scheduled, payment_lines[0].name,
                format='%y%m%d')
            properties.update({'due_date': order_date, 'trans_ser_no': 0})

            total_amount = 0.0
            # Records is a list of tuples (payment_line, generated line).
            # This is to help customization. Head and total row have no
            # associated payment_line
            records.append((None, self._generate_head_record(properties)))
            properties.update({'trans_ser_no': properties['trans_ser_no'] + 1})
            for line in payment_lines:
                if not line.mandate_id or not line.mandate_id.state == "valid":
                    raise exceptions.ValidationError(
                        _('Line with ref %s has no associated valid mandate') %
                        line.name
                    )

                if (payment_order.date_prefered == 'due' and
                        not previous_date == line.ml_maturity_date):
                    records.append((None,
                                    self._generate_total_record(
                                        properties, total_amount)))
                    total_amount = 0.0
                    due_date = export_utils.get_treatment_date(
                        payment_order.date_prefered,
                        line.ml_maturity_date,
                        payment_order.date_scheduled,
                        line.name, format='%y%m%d')
                    properties.update({
                        'dd_order_no': properties['dd_order_no'] + 1,
                        'trans_ser_no': 0,
                        'due_date': due_date})
                    records.append(
                        (None, self._generate_head_record(properties)))
                    properties.update(
                        {'trans_ser_no': properties['trans_ser_no'] + 1})
                    previous_date = line.ml_maturity_date

                records.append((line, self._generate_debit_record(
                    line, properties, payment_order)))
                properties.update(
                    {'nb_transactions': properties.get('nb_transactions') + 1})
                total_amount = total_amount + line.amount_currency
                properties.update(
                    {'trans_ser_no': properties['trans_ser_no'] + 1})

            records.append((None, self._generate_total_record(properties,
                                                              total_amount)))
            properties.update({'dd_order_no': properties['dd_order_no'] + 1})

        records = self._customize_records(records, properties)
        file_content = ''.join(records)  # Concatenate all records
        file_content = file_content.encode('iso8859-1')  # Required encoding
        export_id = self._create_dd_export(active_ids,
                                           overall_amount, properties,
                                           file_content)
        self.write({'banking_export_ch_dd_id': export_id.id,
                    'state': 'finish'})

        action = {
            'name': _('Generated File'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'new',
        }
        return action

    @api.model
    def _generate_head_record(self, properties):
        ''' Head record generation (Transaction type 00) '''
        control_range = self._gen_control_range('00', properties)
        head_record = control_range + export_utils.complete_line(650)

        if len(head_record) == 700:  # Standard head record size
            return head_record
        else:
            raise exceptions.Warning(
                _('Generated head record with size %d is not valid '
                  '(len should be 700)') % len(head_record)
            )

    @api.model
    def _generate_debit_record(self, line, properties, payment_order):
        ''' Convert each payment_line to postfinance debit record
            (Transaction type 47)
        '''
        control_range = self._gen_control_range('47', properties)

        vals = collections.OrderedDict()
        export_utils.check_currency(line, properties)
        self._check_amount(line, properties)
        communications = self._get_communications(line)
        vals.update([
            ('currency', properties.get('currency', 'CHF')),
            ('amount', self._format_number(line.amount_currency, 13)),
            ('reserve_1', export_utils.complete_line(1)),
            ('reserve_2', export_utils.complete_line(3)),
            ('reserve_3', export_utils.complete_line(2)),
            ('deb_account_no', self._get_post_account(line.partner_bank_id)),
            ('reserve_4', export_utils.complete_line(6)),
            ('ref', export_utils.complete_line(27, self._get_ref(line))),
            ('reserve_5', export_utils.complete_line(8)),
            ('deb_address', self._get_account_address(line.partner_bank_id)),
            ('reserve_6', export_utils.complete_line(35)),
            ('reserve_7', export_utils.complete_line(35)),
            ('reserve_8', export_utils.complete_line(35)),
            ('reserve_9', export_utils.complete_line(10)),
            ('reserve_10', export_utils.complete_line(25)),
            ('communication', export_utils.complete_line(140,
                                                         communications)),
            ('reserve_11', export_utils.complete_line(3)),
            ('reserve_12', export_utils.complete_line(1)),
            ('orderer_info', export_utils.complete_line(140)),
            ('reserve_13', export_utils.complete_line(14))
        ])
        debit_record = control_range + ''.join(vals.values())
        if len(debit_record) == 700:  # Standard debit record size
            return debit_record
        else:
            raise exceptions.Warning(
                _('Generated debit_record with size %d is not valid '
                  '(len should be 700)') % len(debit_record)
            )

    @api.model
    def _generate_total_record(self, properties, total_amount):
        ''' Generate total line according to total amount and properties
            (Transaction type 97)
        '''
        control_range = self._gen_control_range('97', properties)

        vals = collections.OrderedDict()
        vals.update([
            ('currency', properties.get('currency', 'CHF')),
            ('nb_transactions', str(
                properties.get('trans_ser_no') -
                1).zfill(6)),
            ('total_amount', self._format_number(total_amount, 13)),
            ('reserve_1', export_utils.complete_line(628)),
        ])
        total_record = control_range + ''.join(vals.values())
        if len(total_record) == 700:
            return total_record
        else:
            raise exceptions.Warning(
                _('Generated total line is not valid (%d instead of 700)') %
                len(total_record)
            )

    @api.model
    def _create_dd_export(self, p_o_ids, total_amount,
                          properties, file_content):
        ''' Create banking.export.ch.dd object '''
        banking_export_ch_dd_obj = self.env['banking.export.ch.dd']
        vals = {
            'payment_order_ids': [(6, 0, [p_o_id for p_o_id in p_o_ids])],
            'total_amount': total_amount,
            'nb_transactions': properties.get('nb_transactions'),
            'file': base64.encodestring(file_content),
            'type': 'Postfinance Direct Debit',
        }
        export_id = banking_export_ch_dd_obj.create(vals)
        return export_id

    @api.one
    def confirm_export(self):
        ''' Save the exported DD file: mark all payments in the file
            as 'sent'. Write 'last debit date' on mandate.
        '''
        self.banking_export_ch_dd_id.write({'state': 'sent'})
        today_str = fields.Date.today()
        for order in self.banking_export_ch_dd_id.payment_order_ids:
            order.signal_workflow('done')
            mandates = order.mapped('line_ids.mandate_id')
            mandates.write({'last_debit_date': today_str})

        # redirect to generated dd export
        action = {
            'name': _('Generated File'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'banking.export.ch.dd',
            'res_id': self.banking_export_ch_dd_id.id,
            'target': 'current',
        }
        return action

    @api.multi
    def cancel_export(self):
        ''' Cancel the export: delete export record '''
        self.banking_export_ch_dd_id.unlink()
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def _customize_records(self, records, properties):
        ''' Use this function if you want to customize the generated lines.
            @param records: list of tuples with tup[0]=payment line and
                              tup[1]=generated string.
            @return: list of strings.
        '''
        return [tup[1] for tup in records]

    ##########################################################################
    #                          Private Tools for DD                          #
    ##########################################################################
    def _check_amount(self, line, properties):
        ''' Max allowed amount is CHF 10'000'000.00 and EUR 5'000'000.00 '''
        if (properties.get('currency') == 'CHF' and
                line.amount_currency > 10000000.00) or (
                    properties.get('currency') == 'EUR' and
                    line.amount_currency > 5000000.00):
            raise exceptions.ValidationError(
                _("Max authorized amount is CHF 10'000'000.00 "
                  "or EUR 5'000'000.00 (%s %.2f given for ref %s)") %
                (properties.get('currency'), line.amount_currency, line.name))

        elif line.amount_currency <= 0:
            raise exceptions.ValidationError(
                _('Amount for line with ref %s is negative (%f '
                  'given)') % (line.name, line.amount_currency)
            )

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
        if bank_account.partner_id:
            line1_owner = bank_account.partner_id.name
        else:
            raise exceptions.ValidationError(
                _('Missing owner name for bank account %s')
                % bank_account.acc_number)

        line2_owner_cmpl = ''
        line3_address = bank_account.bank_id.street or ''
        line4_zip = bank_account.bank_id.zip or ''
        line5_city = bank_account.bank_id.city or ''

        return (export_utils.complete_line(35, line1_owner) +
                export_utils.complete_line(35, line2_owner_cmpl) +
                export_utils.complete_line(35, line3_address) +
                export_utils.complete_line(10, line4_zip) +
                export_utils.complete_line(25, line5_city))

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
            raise exceptions.ValidationError(
                _('Given BV account number is to long ! (%s)') % clean_account
            )
        return clean_account

    def _get_communications(self, line):
        ''' This method can be overloaded to fit your communication style '''
        return ''

    def _get_ref(self, payment_line):
        if export_utils.is_bvr_ref(payment_line.move_line_id.transaction_ref):
            return payment_line.move_line_id.transaction_ref.replace(
                ' ', '').rjust(27, '0')
        return ''

    def _setup_properties(self, payment_order):
        ''' These properties are the same for all lines of the DD file '''
        if not payment_order.company_partner_bank_id.post_dd_identifier:
            raise exceptions.ValidationError(
                _('Missing Postfinance direct debit identifier for account '
                  '%s') % payment_order.company_partner_bank_id.acc_number
            )

        properties = {
            'dd_customer_no':
                payment_order.company_partner_bank_id.post_dd_identifier,
            'dd_order_no': 1,
            'trans_ser_no': 0,
            'nb_transactions': 0,
            'currency': self.currency,
        }

        return properties
