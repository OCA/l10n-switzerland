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
from openerp.osv import orm, fields
from datetime import date, datetime, timedelta
from openerp import netsvc
from openerp.tools import mod10r
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _

import logging
logger = logging.getLogger(__name__)


class lsv_export_wizard(orm.TransientModel):

    ''' LSV file generation wizard. This wizard is called
        when the "make payment" button on a direct debit order
        with payment type "LSV" is pressed
    '''
    _name = 'lsv.export.wizard'
    _description = 'Export LSV Direct Debit File'

    _columns = {
        'treatment_type': fields.selection([
            ('P', _('Production')),
            ('T', _('Test'))], _('Treatment type'), required=True),
        'currency': fields.selection([
            ('CHF', 'CHF'),
            ('EUR', 'EUR')], _('Currency'), required=True),
        'banking_export_ch_dd_id': fields.many2one(
            'banking.export.ch.dd', _('LSV file'), readonly=True),
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
        'treatment_type': 'T',  # FIXME for release
        'currency': 'CHF',
        'state': 'create',
    }

    def generate_lsv_file(self, cr, uid, ids, context=None):
        ''' Generate direct debit export object including the lsv file
            content. Called by generate button.
        '''
        payment_order_obj = self.pool.get('payment.order')
        payment_line_obj = self.pool.get('payment.line')

        active_ids = context.get('active_ids', [])
        if not active_ids:
            raise orm.except_orm('ValueError', _('No payment order selected'))
        payment_order_ids = payment_order_obj.browse(cr, uid, active_ids,
                                                     context)

        # common properties for all lines
        properties = self._setup_properties(cr, uid, context, ids[0],
                                            payment_order_ids[0])

        total_amount = 0.0
        lsv_lines = []

        for payment_order in payment_order_ids:
            total_amount = total_amount + payment_order.total

            ben_bank_id = payment_order.mode.bank_id
            clean_acc_number = ben_bank_id.acc_number.replace(' ', '')
            clean_acc_number = clean_acc_number.replace('-', '')
            ben_address = self._get_account_address(cr, uid, ben_bank_id)
            properties.update({
                'ben_address': ben_address,
                'ben_iban': clean_acc_number,
                'ben_clearing': self._get_clearing(cr, uid,
                                                   payment_order.mode.bank_id),
            })

            if not self._is_ch_li_iban(properties.get('ben_iban')):
                raise orm.except_orm(
                    'ValueError',
                    _('Ben IBAN is not a correct CH or LI IBAN (%s given)') %
                    properties.get('ben_iban'))

            order_by = ''
            if payment_order.date_prefered == 'due':
                order_by = 'account_move_line.date_maturity ASC, '
            order_by += 'payment_line.bank_id'

            # A direct db query is used because order parameter in model.search
            # doesn't support function fields
            cr.execute(
                'SELECT payment_line.id FROM payment_line, account_move_line '
                'WHERE payment_line.move_line_id = account_move_line.id '
                'AND payment_line.order_id = %s '
                'ORDER BY ' + order_by, (payment_order.id,))
            sorted_line_ids = [row[0] for row in cr.fetchall()]
            payment_lines = payment_line_obj.browse(cr, uid, sorted_line_ids,
                                                    context)

            for line in payment_lines:
                if not line.mandate_id or not line.mandate_id.state == "valid":
                    raise orm.except_orm(
                        'RuntimeError',
                        _('Line with ref %s has no associated valid mandate') %
                        line.name)
                # Payment line is associated to generated line to make
                # customizing easier.
                lsv_lines.append((line, self._generate_debit_line(
                    cr, uid, line, properties, payment_order, context)))
                properties.update({'seq_nb': properties['seq_nb'] + 1})

        lsv_lines.append((None, self._generate_total_line(cr, uid, properties,
                                                          total_amount)))

        lsv_lines = self._customize_lines(cr, uid, lsv_lines, properties,
                                          context)
        file_content = ''.join(lsv_lines)  # Concatenate all lines
        file_content = ''.join(
            [ch if ord(ch) < 128 else '?' for ch in file_content])

        export_id = self._create_lsv_export(cr, uid, context, active_ids,
                                            total_amount, properties,
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

    def _generate_debit_line(self, cr, uid, line, properties, payment_order,
                             context=None):
        ''' Convert each payment_line to lsv debit line '''
        deb_acc_number = line.bank_id.acc_number
        deb_acc_number = deb_acc_number.replace(' ', '').replace('-', '')
        if line.bank_id.state == 'iban' and not self._is_ch_li_iban(
                deb_acc_number):
            raise orm.except_orm(
                'ValueError',
                _('Line with ref %s has not a correct CH or LI IBAN'
                  '(%s given)') % (line.name, deb_acc_number))
        vals = collections.OrderedDict()
        vals['TA'] = '875'
        vals['VNR'] = '0'
        vals['VART'] = properties.get('treatment_type', 'P')
        vals['GVDAT'] = self._prepare_date(
            self._get_treatment_date(cr, uid, payment_order.date_prefered,
                                     line.ml_maturity_date,
                                     payment_order.date_scheduled,
                                     line.name))
        vals['BCZP'] = self._complete_line(
            self._get_clearing(cr, uid, line.bank_id), 5)
        vals['EDAT'] = properties.get('edat')
        vals['BCZE'] = self._complete_line(properties.get('ben_clearing'), 5)
        vals['ABSID'] = properties.get('lsv_identifier')
        vals['ESEQ'] = str(properties.get('seq_nb')).zfill(7)
        vals['LSVID'] = properties.get('lsv_identifier')
        self._check_currency(line, properties)
        vals['WHG'] = properties.get('currency', 'CHF')
        self._check_amount(line, properties)
        vals['BETR'] = self._format_number(line.amount_currency, 12)
        vals['KTOZE'] = self._complete_line(properties.get('ben_iban'), 34)
        vals['ADRZE'] = properties.get('ben_address')
        vals['KTOZP'] = self._complete_line(deb_acc_number, 34)
        vals['ADRZP'] = self._get_account_address(cr, uid, line.bank_id)
        vals['MITZP'] = self._complete_line(self._get_communications(cr, uid,
                                                                     line,
                                                                     context),
                                            140)
        ref, ref_type = self._get_ref(cr, uid, context, line)
        vals['REFFL'] = ref_type
        vals['REFNR'] = self._complete_line(ref, 27)
        if vals['REFFL'] == 'A':
            if not properties.get('esr_party_number'):
                raise orm.except_orm(
                    'ValueError',
                    _('Line with ref %s has ESR ref, but no valid '
                      'ESR party number exists for ben account') %
                    line.name)
            vals['ESRTN'] = self._complete_line(
                properties.get('esr_party_number'),
                9)
        else:
            vals['ESRTN'] = self._complete_line('', 9)
        gen_line = ''.join(vals.values())
        if len(gen_line) == 588:  # Standard 875 line size
            return gen_line
        else:
            raise orm.except_orm(
                'RuntimeError',
                _('Generated line for ref %s with size %d is not valid '
                  '(len should be 588)') %
                (line.name, len(gen_line)))

    def _generate_total_line(self, cr, uid, properties, total_amount):
        ''' Generate total line according to total amount and properties '''
        vals = collections.OrderedDict()
        vals['TA'] = '890'
        vals['VNR'] = '0'
        vals['EDAT'] = properties.get('edat')
        vals['ABSID'] = properties.get('lsv_identifier')
        vals['ESEQ'] = str(properties.get('seq_nb')).zfill(7)
        vals['WHG'] = properties.get('currency', 'CHF')
        vals['TBETR'] = self._format_number(total_amount, 16)

        line = ''.join(vals.values())
        if len(line) == 43:
            return line
        else:
            raise orm.except_orm(
                'RuntimeError',
                _('Generated total line is not valid (%d instead of 43)') %
                len(line))

    def _create_lsv_export(self, cr, uid, context, p_o_ids, total_amount,
                           properties, file_content):
        ''' Create banking.export.ch.dd object '''
        banking_export_ch_dd_obj = self.pool.get('banking.export.ch.dd')
        vals = {
            'payment_order_ids': [(6, 0, [p_o_id for p_o_id in p_o_ids])],
            'total_amount': total_amount,
            # Substract 1 for total line
            'nb_transactions': properties.get('seq_nb') - 1,
            'file': base64.encodestring(file_content),
            'type': 'LSV',
        }
        export_id = banking_export_ch_dd_obj.create(cr, uid, vals,
                                                    context=context)
        return export_id

    def confirm_export(self, cr, uid, ids, context=None):
        ''' Save the exported LSV file: mark all payments in the file
            as 'sent'. Write 'last debit date' on mandate.
        '''
        export_wizard = self.browse(cr, uid, ids[0], context=context)
        self.pool.get('banking.export.ch.dd').write(
            cr, uid, export_wizard.banking_export_ch_dd_id.id, {
                'state': 'sent'}, context=context)
        wf_service = netsvc.LocalService('workflow')
        today_str = datetime.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
        for order in export_wizard.banking_export_ch_dd_id.payment_order_ids:
            wf_service.trg_validate(uid, 'payment.order', order.id, 'done', cr)
            mandate_ids = [line.mandate_id.id for line in order.line_ids]
            self.pool['account.banking.mandate'].write(
                cr, uid, mandate_ids, {
                    'last_debit_date': today_str}, context=context)

        # redirect to generated lsv export
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

    def _customize_lines(self, cr, uid, lsv_lines, properties, context=None):
        ''' Use this if you want to customize the generated lines.
            @param lsv_lines: list of tuples with tup[0]=payment line
                              and tup[1]=generated string.
            @return: list of strings.
        '''
        return [tup[1] for tup in lsv_lines]

    ##########################
    #         Tools          #
    ##########################
    def _check_amount(self, line, properties):
        ''' Max allowed amount is CHF 99'999'999.99.
            We need to also check EUR values...
        '''
        if (properties.get('currency') == 'CHF' and
            line.amount_currency > 99999999.99) or (
                properties.get('currency') == 'EUR' and
                line.amount_currency > 99999999.99 / properties.get('rate')):
            raise orm.except_orm(
                'ValueError',
                _('Stop kidding... max authorized amount is CHF 99 999 999.99 '
                  '(%.2f %s given for ref %s)') %
                (line.amount_currency, properties.get('currency'), line.name))
        elif line.amount_currency <= 0:
            raise orm.except_orm(
                'ValueError',
                _('Amount for line with ref %s is negative (%f given)') %
                (line.name, line.amount_currency))

    def _check_currency(self, line, properties):
        ''' Check that line currency is equal to lsv export currency '''
        if not line.currency.name == properties.get(
                'currency'):  # All currencies have to be the same !
            raise orm.except_orm(
                'ValueError',
                _('Line with ref %s has %s currency and lsv file %s '
                  '(should be the same)') %
                (line.name, line.currency.name, properties.get(
                    'currency', '')))

    def _complete_line(self, string, nb_char):
        ''' In LSV file each field has a defined length.
            This way, lines have to be filled with spaces
        '''
        if len(string) > nb_char:
            return string[:nb_char]

        return string.ljust(nb_char)

    def _format_number(self, amount, nb_char):
        ''' Accepted formats are "00000000123,", "0000000123,1"
            and "000000123,46".
            This function always returns the last format
        '''
        amount_str = '{:.2f}'.format(amount).replace('.', ',').zfill(nb_char)
        return amount_str

    def _get_account_address(self, cr, uid, bank_account):
        ''' Return account address for given bank_account.
            First 2 lines are mandatory !
        '''
        if bank_account.owner_name:
            bank_line1 = bank_account.owner_name
        else:
            raise orm.except_orm('ValueError',
                                 _('Missing owner name for bank account %s')
                                 % bank_account.acc_number)

        bank_line2 = bank_account.street if bank_account.street else ''
        bank_line3 = bank_account.zip + ' ' + bank_account.city \
            if bank_account.zip and bank_account.city else ''
        bank_line4 = bank_account.country_id.name \
            if bank_account.country_id else ''

        # line2 is empty, we try to fill with something else
        if not bank_line2:
            if bank_line3:
                bank_line2 = bank_line3
                bank_line3 = bank_line4
                bank_line4 = ''
            elif bank_line4:
                bank_line2 = bank_line4
                bank_line4 = ''
            else:
                raise orm.except_orm('ValueError',
                                     _('Missing address for bank account %s')
                                     % bank_account.acc_number)

        return (self._complete_line(bank_line1, 35) +
                self._complete_line(bank_line2, 35) +
                self._complete_line(bank_line3, 35) +
                self._complete_line(bank_line4, 35))

    def _get_clearing(self, cr, uid, bank_account):
        clearing = ''
        if bank_account.bank.clearing:
            clearing = bank_account.bank.clearing
        elif bank_account.state == 'iban':
            clean_acc_number = bank_account.acc_number.replace(" ", "")
            # Clearing number is always 5 chars and starts at position 5
            # (4 in machine-index) in CH-iban
            clearing = str(int(clean_acc_number[4:9]))
        else:
            raise orm.except_orm(
                'RuntimeError',
                _('Unable to determine clearing number for account %s') %
                bank_account.acc_number)

        return clearing

    def _get_communications(self, cr, uid, line, context):
        ''' This method can be overloaded to fit your communication style '''
        return ''

    def _get_ref(self, cr, uid, context, payment_line):
        if self._is_bvr_ref(
                cr,
                uid,
                payment_line.move_line_id.transaction_ref):
            return payment_line.move_line_id.transaction_ref.replace(
                ' ', '').rjust(27, '0'), 'A'
        else:
            return '', 'B'  # If anyone uses IPI reference, get it here

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

    def _get_treatment_date(self, cr, uid, prefered_type, line_mat_date,
                            order_sched_date, name):
        ''' Returns appropriate date according to payment_order and
            payment_order_line data.
            Raises an error if treatment date is > today+30 or < today-10
        '''
        requested_date = date.today()
        if prefered_type == 'due':
            requested_date = datetime.strptime(line_mat_date, DEFAULT_SERVER_DATE_FORMAT).date() \
                or requested_date
        elif prefered_type == 'fixed':
            requested_date = datetime.strptime(order_sched_date, DEFAULT_SERVER_DATE_FORMAT).date() \
                or requested_date

        if requested_date > date.today() + timedelta(days=30) \
                or requested_date < date.today() - timedelta(days=10):
            raise orm.except_orm(
                'ValueError', _('Incorrect treatment date: %s for line with '
                                'ref %s') % (requested_date, name))

        return requested_date

    def _is_ch_li_iban(self, iban):
        ''' Check if given iban is valid ch or li iban '''
        IBAN_CHAR_MAP = {
            "A": "10",
            "B": "11",
            "C": "12",
            "D": "13",
            "E": "14",
            "F": "15",
            "G": "16",
            "H": "17",
            "I": "18",
            "J": "19",
            "K": "20",
            "L": "21",
            "M": "22",
            "N": "23",
            "O": "24",
            "P": "25",
            "Q": "26",
            "R": "27",
            "S": "28",
            "T": "29",
            "U": "30",
            "V": "31",
            "W": "32",
            "X": "33",
            "Y": "34",
            "Z": "35"}
        iban_validation_str = self._replace_all(
            iban[
                4:] +
            iban[
                0:4],
            IBAN_CHAR_MAP)
        valid = len(iban) == 21
        valid &= iban[0:2].lower() in ['ch', 'li']
        valid &= (int(iban_validation_str) % 97) == 1
        return valid

    def _prepare_date(self, format_date):
        ''' Returns date formatted to YYYYMMDD string '''
        return format_date.strftime('%Y%m%d')

    def _replace_all(self, text, char_map):
        ''' Replace the char_map in text '''
        for k, v in char_map.iteritems():
            text = text.replace(k, v)
        return text

    def _setup_properties(self, cr, uid, context, wizard_id, payment_order):
        ''' These properties are the same for all lines of the LSV file '''
        form = self.browse(cr, uid, wizard_id, context)
        if not payment_order.mode.bank_id.lsv_identifier:
            raise orm.except_orm('ValueError',
                                 _('Missing LSV identifier for account %s')
                                 % payment_order.mode.bank_id.acc_number)
        currency_obj = self.pool.get('res.currency')
        chf_id = currency_obj.search(cr, uid, [('name', '=', 'CHF')])
        rate = currency_obj.read(cr, uid, chf_id[0], ['rate_silent'],
                                 context)['rate_silent']

        ben_bank_id = payment_order.mode.bank_id
        properties = {
            'treatment_type': form.treatment_type,
            'currency': form.currency,
            'seq_nb': 1,
            'lsv_identifier': ben_bank_id.lsv_identifier.upper(),
            'esr_party_number': ben_bank_id.esr_party_number,
            'edat': self._prepare_date(
                date.today()),
            'rate': rate,
        }

        return properties
