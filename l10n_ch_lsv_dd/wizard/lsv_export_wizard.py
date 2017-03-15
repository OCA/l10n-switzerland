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
import string
from datetime import date
from . import export_utils

from openerp import models, fields, api, _, exceptions

import logging
logger = logging.getLogger(__name__)


# Mapping between Latin-1 to ascii characters, used for LSV.
LSV_LATIN1_TO_ASCII_MAPPING = {
    32: ' ', 33: '.', 34: '.', 35: '.', 36: '.', 37: '.', 38: '+', 39: "'",
    40: '(', 41: ')', 42: '.', 43: '+', 44: ',', 45: '-', 46: '.', 47: '/',
    48: '0', 49: '1', 50: '2', 51: '3', 52: '4', 53: '5', 54: '6', 55: '7',
    56: '8', 57: '9', 58: ':', 59: '.', 60: '.', 61: '.', 62: '.', 63: '?',
    64: '.', 65: 'A', 66: 'B', 67: 'C', 68: 'D', 69: 'E', 70: 'F', 71: 'G',
    72: 'H', 73: 'I', 74: 'J', 75: 'K', 76: 'L', 77: 'M', 78: 'N', 79: 'O',
    80: 'P', 81: 'Q', 82: 'R', 83: 'S', 84: 'T', 85: 'U', 86: 'V', 87: 'W',
    88: 'X', 89: 'Y', 90: 'Z', 91: '.', 92: '.', 93: '.', 94: '.', 95: '.',
    96: '.', 97: 'a', 98: 'b', 99: 'c', 100: 'd', 101: 'e', 102: 'f', 103: 'g',
    104: 'h', 105: 'i', 106: 'j', 107: 'k', 108: 'l', 109: 'm', 110: 'n',
    111: 'o', 112: 'p', 113: 'q', 114: 'r', 115: 's', 116: 't', 117: 'u',
    118: 'v', 119: 'w', 120: 'x', 121: 'y', 122: 'z', 123: '.', 124: '.',
    125: '.', 126: '.', 127: '.', 128: ' ', 129: ' ', 130: ' ', 131: ' ',
    132: ' ', 133: ' ', 134: ' ', 135: ' ', 136: ' ', 137: ' ', 138: ' ',
    139: ' ', 140: ' ', 141: ' ', 142: ' ', 143: ' ', 144: ' ', 145: ' ',
    146: ' ', 147: ' ', 148: ' ', 149: ' ', 150: ' ', 151: ' ', 152: ' ',
    153: ' ', 154: ' ', 155: ' ', 156: ' ', 157: ' ', 158: ' ', 159: ' ',
    160: '.', 161: '.', 162: '.', 163: '.', 164: '.', 165: '.', 166: '.',
    167: '.', 168: '.', 169: '.', 170: '.', 171: '.', 172: '.', 173: '.',
    174: '.', 175: '.', 176: '.', 177: '.', 178: '.', 179: '.', 180: '.',
    181: '.', 182: '.', 183: '.', 184: '.', 185: '.', 186: '.', 187: '.',
    188: '.', 189: '.', 190: '.', 191: '.', 192: 'A', 193: 'A', 194: 'A',
    195: 'A', 196: 'EA', 197: 'A', 198: 'EA', 199: 'C', 200: 'E', 201: 'E',
    202: 'E', 203: 'E', 204: 'I', 205: 'I', 206: 'I', 207: 'I', 208: '.',
    209: 'N', 210: 'O', 211: 'O', 212: 'O', 213: 'O', 214: 'EO', 215: '.',
    216: '.', 217: 'U', 218: 'U', 219: 'U', 220: 'EU', 221: 'Y', 222: '.',
    223: 'ss', 224: 'a', 225: 'a', 226: 'a', 227: 'a', 228: 'ea', 229: 'a',
    230: 'ea', 231: 'c', 232: 'e', 233: 'e', 234: 'e', 235: 'e', 236: 'i',
    237: 'i', 238: 'i', 239: 'i', 240: '.', 241: 'n', 242: 'o', 243: 'o',
    244: 'o', 245: 'o', 246: 'eo', 247: '.', 248: '.', 249: 'u', 250: 'u',
    251: 'u', 252: 'eu', 253: 'y', 254: '.', 255: 'y',
}


class LsvExportWizard(models.TransientModel):

    ''' LSV file generation wizard. This wizard is called
        when the "make payment" button on a direct debit order
        with payment type "LSV" is pressed

        In version 8, this wizard was called from the option in the More
        menu of a payment.order, but in version 9, to force the use of the
        workflow, we removed the entries in the menu. To avoid moving around
        the existing code, the wizard was kept (although now it can not
        be launched, but only instantiated to be used).
    '''
    _name = 'lsv.export.wizard'
    _description = 'Export LSV Direct Debit File'

    treatment_type = fields.Selection(
        [('P', _('Production')), ('T', _('Test'))],
        required=True,
        default='T'     # FIXME for release
    )
    currency = fields.Selection(
        [('CHF', 'CHF'),
         ('EUR', 'EUR'),
         ],
        required=True,
        default='CHF'
    )
    banking_export_ch_dd_id = fields.Many2one(
        'banking.export.ch.dd',
        'LSV file',
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
        related='banking_export_ch_dd_id.nb_transactions'
    )
    total_amount = fields.Float(
        related='banking_export_ch_dd_id.total_amount'
    )
    state = fields.Selection(
        [('create', _('Create')), ('finish', _('Finish'))],
        readonly=True,
        default='create'
    )

    @api.multi
    def generate_lsv_file(self):
        ''' Generate direct debit export object including the lsv file
            content. Called by generate button.
        '''
        self.ensure_one()
        payment_order_obj = self.env['account.payment.order']
        payment_line_obj = self.env['account.payment.line']

        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            raise exceptions.ValidationError(_('No payment order selected'))
        payment_orders = payment_order_obj.browse(active_ids)

        # common properties for all lines
        properties = self._setup_properties(payment_orders[0])

        total_amount = 0.0
        lsv_lines = []

        for payment_order in payment_orders:
            total_amount = total_amount + payment_order.total_company_currency

            ben_bank = payment_order.company_partner_bank_id
            clean_acc_number = ben_bank.acc_number.replace(' ', '')
            clean_acc_number = clean_acc_number.replace('-', '')
            ben_address = self._get_account_address(ben_bank)
            properties.update({
                'ben_address': ben_address,
                'ben_iban': clean_acc_number,
                'ben_clearing':
                    self._get_clearing(payment_order.company_partner_bank_id),
            })

            if not self._is_ch_li_iban(properties.get('ben_iban')):
                raise exceptions.ValidationError(
                    _('Ben IBAN is not a correct CH or LI IBAN (%s given)') %
                    properties.get('ben_iban')
                )

            order_by = ''
            if payment_order.date_prefered == 'due':
                order_by = 'account_move_line.date_maturity ASC, '
            order_by += 'account_payment_line.partner_bank_id'

            # A direct db query is used because order parameter in model.search
            # doesn't support function fields
            self.env.cr.execute("""
                SELECT account_payment_line.id
                FROM account_payment_line, account_move_line
                WHERE account_payment_line.move_line_id = account_move_line.id
                AND account_payment_line.order_id = %s
                ORDER BY """ + order_by, (payment_order.id,))
            sorted_line_ids = [row[0] for row in self.env.cr.fetchall()]
            payment_lines = payment_line_obj.browse(sorted_line_ids)

            for line in payment_lines:
                if not line.mandate_id or not line.mandate_id.state == "valid":
                    raise exceptions.ValidationError(
                        _('Line with ref %s has no associated valid mandate') %
                        line.name
                    )

                # Payment line is associated to generated line to make
                # customizing easier.
                lsv_lines.append((line, self._generate_debit_line(
                    line, properties, payment_order)))
                properties.update({'seq_nb': properties['seq_nb'] + 1})

        lsv_lines.append((None, self._generate_total_line(properties,
                                                          total_amount)))

        lsv_lines = self._customize_lines(lsv_lines, properties)
        file_content = ''.join(lsv_lines)  # Concatenate all lines
        file_content = ''.join(
            [LSV_LATIN1_TO_ASCII_MAPPING.get(ord(ch), ch)
             for ch in file_content])

        export_id = self._create_lsv_export(active_ids,
                                            total_amount,
                                            properties,
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
    def _generate_debit_line(self, line, properties, payment_order):
        ''' Convert each payment_line to lsv debit line '''
        deb_acc_number = line.partner_bank_id.acc_number
        deb_acc_number = deb_acc_number.replace(' ', '').replace('-', '')
        if line.partner_bank_id.acc_type == 'iban' and not self._is_ch_li_iban(
                deb_acc_number):
            raise exceptions.ValidationError(
                _('Line with ref %s has not a correct CH or LI IBAN'
                  '(%s given)') % (line.name, deb_acc_number)
            )
        vals = collections.OrderedDict()
        vals['TA'] = '875'
        vals['VNR'] = '0'
        vals['VART'] = properties.get('treatment_type', 'P')
        vals['GVDAT'] = export_utils.get_treatment_date(
            payment_order.date_prefered, line.ml_maturity_date,
            payment_order.date_scheduled, line.name)
        vals['BCZP'] = export_utils.complete_line(
            5, self._get_clearing(line.partner_bank_id))
        vals['EDAT'] = properties.get('edat')
        vals['BCZE'] = export_utils.complete_line(
            5, properties.get('ben_clearing'))
        vals['ABSID'] = properties.get('lsv_identifier')
        vals['ESEQ'] = str(properties.get('seq_nb')).zfill(7)
        vals['LSVID'] = properties.get('lsv_identifier')
        export_utils.check_currency(line, properties)
        vals['WHG'] = properties.get('currency', 'CHF')
        self._check_amount(line, properties)
        vals['BETR'] = self._format_number(line.amount_currency, 12)
        vals['KTOZE'] = export_utils.complete_line(
            34, properties.get('ben_iban'))
        vals['ADRZE'] = properties.get('ben_address')
        vals['KTOZP'] = export_utils.complete_line(34, deb_acc_number)
        vals['ADRZP'] = self._get_account_address(line.partner_bank_id)
        vals['MITZP'] = export_utils.complete_line(
            140, self._get_communications(line))
        ref, ref_type = self._get_ref(line)
        vals['REFFL'] = ref_type
        vals['REFNR'] = export_utils.complete_line(27, ref)
        if vals['REFFL'] == 'A':
            if not properties.get('esr_party_number'):
                raise exceptions.ValidationError(
                    _('Line with ref %s has ESR ref, but no valid '
                      'ESR party number exists for ben account') %
                    line.name
                )
            vals['ESRTN'] = export_utils.complete_line(
                9, properties.get('esr_party_number'))
        else:
            vals['ESRTN'] = export_utils.complete_line(9)
        gen_line = ''.join(vals.values())
        if len(gen_line) == 588:  # Standard 875 line size
            return gen_line
        else:
            raise exceptions.Warning(
                _('Generated line for ref %s with size %d is not valid '
                  '(len should be 588)') %
                (line.name, len(gen_line))
            )

    def _generate_total_line(self, properties, total_amount):
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
            raise exceptions.Warning(
                _('Generated total line is not valid (%d instead of 43)') %
                len(line)
            )

    def _create_lsv_export(self, p_o_ids, total_amount,
                           properties, file_content):
        ''' Create banking.export.ch.dd object '''
        banking_export_ch_dd_obj = self.env['banking.export.ch.dd']
        vals = {
            'payment_order_ids': [(6, 0, p_o_ids)],
            'total_amount': total_amount,
            # Substract 1 for total line
            'nb_transactions': properties.get('seq_nb') - 1,
            'file': base64.encodestring(file_content),
            'type': 'LSV',
        }
        export_id = banking_export_ch_dd_obj.create(vals)
        return export_id

    @api.multi
    def confirm_export(self):
        ''' Save the exported LSV file: mark all payments in the file
            as 'sent'. Write 'last debit date' on mandate.
        '''
        self.banking_export_ch_dd_id.write({'state': 'sent'})
        today_str = fields.Date.today()

        for order in self.banking_export_ch_dd_id.payment_order_ids:
            order.signal_workflow('done')
            mandates = order.mapped('line_ids.mandate_id')
            mandates.write({'last_debit_date': today_str})

        # redirect to generated lsv export
        action = {
            'name': 'Generated File',
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
    def _customize_lines(self, lsv_lines, properties):
        ''' Use this if you want to customize the generated lines.
            @param lsv_lines: list of tuples with tup[0]=payment line
                              and tup[1]=generated string.
            @return: list of strings.
        '''
        return [tup[1] for tup in lsv_lines]

    ##########################################################################
    #                         Private Tools for LSV                          #
    ##########################################################################
    def _check_amount(self, line, properties):
        ''' Max allowed amount is CHF 99'999'999.99.
            We need to also check EUR values...
        '''
        if (properties.get('currency') == 'CHF' and
            line.amount_currency > 99999999.99) or (
                properties.get('currency') == 'EUR' and
                line.amount_currency > 99999999.99 / properties.get('rate')):
            raise exceptions.ValidationError(
                _('Stop kidding... max authorized amount is CHF 99 999 999.99 '
                  '(%.2f %s given for ref %s)') %
                (line.amount_currency, properties.get('currency'), line.name))

        elif line.amount_currency <= 0:
            raise exceptions.ValidationError(
                _('Amount for line with ref %s is negative (%f given)') %
                (line.name, line.amount_currency))

    def _format_number(self, amount, nb_char):
        ''' Accepted formats are "00000000123,", "0000000123,1"
            and "000000123,46".
            This function always returns the last format
        '''
        amount_str = '{:.2f}'.format(amount).replace('.', ',').zfill(nb_char)
        return amount_str

    def _get_account_address(self, bank_account):
        ''' Return account address for given bank_account.
            First 2 lines are mandatory !
        '''
        if bank_account.partner_id:
            bank_line1 = bank_account.partner_id.name
        else:
            raise exceptions.ValidationError(
                _('Missing owner name for bank account %s')
                % bank_account.acc_number)

        bank_line2 = bank_account.bank_id.street or ''
        bank_line3 = \
            bank_account.bank_id.zip + ' ' + bank_account.bank_id.city \
            if bank_account.bank_id.zip and bank_account.bank_id.city else ''
        bank_line4 = bank_account.bank_id.country.name or ''

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
                raise exceptions.ValidationError(
                    _('Missing address for bank account %s')
                    % bank_account.acc_number)

        return (export_utils.complete_line(35, bank_line1) +
                export_utils.complete_line(35, bank_line2) +
                export_utils.complete_line(35, bank_line3) +
                export_utils.complete_line(35, bank_line4))

    def _get_clearing(self, bank_account):
        clearing = ''
        if bank_account.bank_id.clearing:
            clearing = bank_account.bank_id.clearing
        elif bank_account.acc_type == 'iban':
            clean_acc_number = bank_account.acc_number.replace(" ", "")
            # Clearing number is always 5 chars and starts at position 5
            # (4 in machine-index) in CH-iban
            clearing = str(int(clean_acc_number[4:9]))
        else:
            raise exceptions.ValidationError(
                _('Unable to determine clearing number for account %s') %
                bank_account.acc_number)

        return clearing

    def _get_communications(self, line):
        ''' This method can be overloaded to fit your communication style '''
        return ''

    def _get_ref(self, payment_line):
        if export_utils.is_bvr_ref(payment_line.move_line_id.transaction_ref):
            return payment_line.move_line_id.transaction_ref.replace(
                ' ', '').rjust(27, '0'), 'A'
        return '', 'B'  # If anyone uses IPI reference, get it here

    def _is_ch_li_iban(self, iban):
        ''' Check if given iban is valid ch or li iban '''
        IBAN_CHAR_MAP = dict(
            (string.uppercase[i], str(10 + i)) for i in range(26))
        iban_validation_str = self._replace_all(
            iban[4:] + iban[0:4], IBAN_CHAR_MAP)
        valid = len(iban) == 21
        valid &= iban[0:2].lower() in ['ch', 'li']
        valid &= (int(iban_validation_str) % 97) == 1
        return valid

    def _replace_all(self, text, char_map):
        ''' Replace the char_map in text '''
        for k, v in char_map.iteritems():
            text = text.replace(k, v)
        return text

    def _setup_properties(self, payment_order):
        ''' These properties are the same for all lines of the LSV file '''
        if not payment_order.company_partner_bank_id.lsv_identifier:
            raise exceptions.ValidationError(
                _('Missing LSV identifier for account %s')
                % payment_order.company_partner_bank_id.acc_number)

        currency_obj = self.env['res.currency']
        chf_currency = currency_obj.search([('name', '=', 'CHF')])
        rate = chf_currency.rate
        ben_bank = payment_order.company_partner_bank_id
        properties = {
            'treatment_type': self.treatment_type,
            'currency': self.currency,
            'seq_nb': 1,
            'lsv_identifier': ben_bank.lsv_identifier.upper(),
            'esr_party_number': ben_bank.esr_party_number,
            'edat': date.today().strftime('%Y%m%d'),
            'rate': rate,
        }
        return properties
