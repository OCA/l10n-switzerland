# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville
#    Copyright 2015 Camptocamp SA
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

import sys
import traceback
import logging
import base64
import csv
import tempfile
from openerp import models, fields, api, exceptions
from openerp.tools.translate import _
from itertools import izip_longest
from datetime import datetime

_logger = logging.getLogger(__name__)


class AccountCresusImport(models.TransientModel):
    _name = 'account.cresus.import'
    _description = 'Export Accounting'

    company_id = fields.Many2one('res.company', 'Company',
                                 invisible=True)
    period_id = fields.Many2one('account.period', 'Period',
                                required=True)
    report = fields.Text(
        'Report',
        readonly=True
        )
    journal_id = fields.Many2one('account.journal', 'Journal',
                                 required=True)
    state = fields.Char(sting="Import state"
                        'Report',
                        readonly=True,
                        default="draft"
                        )
    file = fields.Binary(
        'File',
        required=True
        )
    imported_move_ids = fields.Many2many(
        'account.move', 'import_cresus_move_rel',
        string='Imported moves')

    help_html = fields.Html('Import help', readonly=True,
                            default=_('''
                 In order to import your 'Cresus Salaires' .txt \
                 file you must complete the following requirements : </br>
                * The accounts, analytical accounts used in the Cresus\
                 file must be previously created into Odoo  </br>
                * The date of the entry will determine the period used\
                 in Odoo, so please ensure the period is created already. </br>
                * If the Cresus file uses VAT codes (i.e: IPI), \
                please make sure you have indicated this code in the \
                related Odoo tax (new field). \
                Warning, the Odoo tax must be 'tax included'. \
                If the tax does not exist you have to create it. </br>
                * All PL accounts must have a deferral method = 'none'\
                (meaning: no balance brought forward in the new fiscal year)\
                and all
                 Balance sheet account must have a deferral \
                method = 'balance'. </br>'''))

    HEAD_CRESUS = ['date', 'debit', 'credit', 'pce',
                   'ref', 'amount', 'typtvat', 'currency_amount',
                   'analytic_account']
    HEAD_ODOO = ['ref', 'date', 'period_id', 'journal_id',
                 'line_id/account_id', 'line_id/partner_id', 'line_id/name',
                 'line_id/debit', 'line_id/credit',
                 'line_id/account_tax_id',
                 'line_id/analytic_account_id']

    @api.multi
    def open_account_moves(self):
        res = {
            'domain': str([('id', 'in', self.imported_move_ids.ids)]),
            'name': 'Account Move',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }
        return res

    def format_messages(self, messages):
        """Format error messages generated by the BaseModel.load method

        :param messages: return of BaseModel.load messages key
        :returns: formatted string

        """
        res = []
        for msg in messages:
            rows = msg.get('rows', {})
            res.append(_("%s. -- Field: %s -- rows %s to %s") % (
                msg.get('message', 'N/A'),
                msg.get('field', 'N/A'),
                rows.get('from', 'N/A'),
                rows.get('to', 'N/A'))
            )
        return "\n \n".join(res)

    def _parse_csv(self):
        """Parse stored CSV file in order to be usable by BaseModel.load method.

        Manage base 64 decoding.

        :param imp_id: current importer id
        :returns: (head [list of first row], data [list of list])

        """
        # We use tempfile in order to avoid memory error with large files
        with tempfile.TemporaryFile() as src:
            content = self.file
            delimiter = '\t'
            src.write(content)
            with tempfile.TemporaryFile() as decoded:
                src.seek(0)
                base64.decode(src, decoded)
                decoded.seek(0)
                return self._prepare_csv_data(decoded, delimiter)

    def _prepare_csv_data(self, csv_file, delimiter=","):
        """Parse a decoded CSV file and return head list and data list

        :param csv_file: decoded CSV file
        :param delimiter: CSV file delimiter char
        :returns: (head [list of first row], data [list of list])

        """
        try:
            data = csv.DictReader(csv_file, fieldnames=self.HEAD_CRESUS,
                                  delimiter=delimiter)
        except csv.Error as error:
            raise exceptions.Warning(
                _('CSV file is malformed'),
                _("Please choose the correct separator \n"
                  "the error detail is : \n %s") % repr(error)
            )
        # Generator does not work with orm.BaseModel.load
        values = [x for x in data if x]

        return (values)

    def _manage_load_results(self, result):
        """Manage the BaseModel.load function output and store exception.

        Will generate success/failure report and store it into report field.
        Manage commit and rollback even if load method uses PostgreSQL
        Savepoints.

        :param result: BaseModel.load returns
                       {ids: list(int)|False, messages: [Message]}
        """
        # Import sucessful
        if not result['messages']:
            self.state = 'done'
            self.report = _("Lines imported")
            self.imported_move_ids = result['ids']
        else:
            self.report = self.format_messages(result['messages'])
            self.state = 'error'

    @api.multi
    def _standardise_data(self, data):
        """ This function split one line of the CSV into multiple lines.
        Cresus just write one line per move,
        """
        new_openerp_data = []
        tax_obj = self.env['account.tax']
        account_obj = self.env['account.account']
        standard_dict = dict(izip_longest(self.HEAD_ODOO, []))
        previous_date = False
        for line_cresus in data:
            is_negative = False
            current_date_french_format = datetime.strptime(line_cresus['date'],
                                                           '%d.%m.%Y')
            current_openerp_date = fields.Date.to_string(
                current_date_french_format)
            default_value = standard_dict.copy()
            if (not previous_date) or previous_date != current_openerp_date:
                default_value.update({'date': current_openerp_date,
                                      'ref': line_cresus['pce'],
                                      'journal_id': self.journal_id.name,
                                      'period_id': self.period_id.code
                                      })
                previous_date = current_openerp_date
            else:
                default_value.update({'date': None,
                                      'ref': None,
                                      'journal_id': None,
                                      'period_id': None})
            decimal_amount = float(
                line_cresus['amount'].replace('\'', '').replace(' ', ''))
            if decimal_amount < 0:
                default_value.update({'line_id/credit': abs(decimal_amount),
                                      'line_id/debit': 0.0,
                                      'line_id/account_id':
                                      line_cresus['debit']})
                is_negative = True
            else:
                default_value.update({'line_id/debit': abs(decimal_amount),
                                      'line_id/credit': 0.0,
                                      'line_id/account_id':
                                      line_cresus['debit']})
            tax_code = None
            analytic_code = None
            tax_code_inverted = None
            tax_current = None
            analytic_code_inverted = None
            if line_cresus['typtvat']:
                tax_current = tax_obj.search([('tax_cresus_mapping',
                                               '=',
                                               line_cresus['typtvat']),
                                              ('price_include', '=', True)],
                                             limit=1)
            if tax_current or line_cresus['analytic_account']:
                current_account = account_obj.search(
                    [('code', '=', default_value['line_id/account_id'])],
                    limit=1)
                if current_account:
                    # Search for account that have a deferal method
                    if current_account.user_type.close_method == 'none':
                        if tax_current:
                            tax_code = tax_current.name
                        analytic_code = line_cresus['analytic_account']
            default_value.update({'line_id/account_tax_id': tax_code,
                                  'line_id/partner_id': False,
                                  'line_id/name': line_cresus['ref'],
                                  'line_id/analytic_account_id':
                                  analytic_code})
            new_openerp_data.append(default_value)
            #
            # Generated the second line inverted
            #
            inverted_default_value = default_value.copy()
            inverted_default_value.update({'date': None,
                                           'ref': None,
                                           'journal_id': None,
                                           'period_id': None})
            if is_negative:
                inverted_default_value.update({'line_id/debit':
                                               abs(decimal_amount),
                                               'line_id/credit': 0.0,
                                               'line_id/account_id':
                                               line_cresus['credit']})
            else:
                inverted_default_value.update({'line_id/debit': 0.0,
                                               'line_id/credit':
                                               abs(decimal_amount),
                                               'line_id/account_id':
                                               line_cresus['credit']})
                # Search for account that have a deferal method
            if tax_current or line_cresus['analytic_account']:
                current_account = account_obj.search([
                    ('code', '=',
                     inverted_default_value.get('line_id/account_id'))])
                if current_account:
                    if current_account.user_type.close_method == 'none':
                        if tax_current:
                            tax_code_inverted = tax_current['name']
                    analytic_code_inverted = line_cresus['analytic_account']
            inverted_default_value.update({'line_id/account_tax_id':
                                           tax_code_inverted,
                                          'line_id/analytic_account_id':
                                           analytic_code_inverted})
            new_openerp_data.append(inverted_default_value)

        return new_openerp_data

    @api.multi
    def _load_data(self, data):
        """Function that does the load of parsed CSV file.

        If will log exception and susccess into the report fields.

        :param data: CSV file content (list of data list)
        """
        # Change data from dict to list of array
        data_array = []
        for data_item_dict in data:
            data_item = []
            for item in self.HEAD_ODOO:
                data_item.append(data_item_dict[item])
            data_array.append(data_item)
        try:
            res = self.env['account.move'].load(self.HEAD_ODOO,
                                                data_array)

            self._manage_load_results(res)
        except Exception as exc:
            ex_type, sys_exc, tb = sys.exc_info()
            tb_msg = ''.join(traceback.format_tb(tb, 30))
            _logger.error(tb_msg)
            _logger.error(repr(exc))
            self.report = _("Unexpected exception.\n %s \n %s" %
                            (repr(exc), tb_msg))
            self.state = 'error'
        finally:
            if self.state == 'error':
                self.env.cr.rollback()
                self.write({'report': self.report, 'state': self.state})
        return {}

    @api.multi
    def import_file(self):
        data = self._parse_csv()
        new_data = self._standardise_data(data)
        return self._load_data(new_data)
