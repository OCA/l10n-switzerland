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
from lxml import etree
from itertools import izip_longest
from StringIO import StringIO
from openerp import models, fields, api, _

_logger = logging.getLogger(__name__)


class AccountWinbizImport(models.TransientModel):
    _name = 'account.winbiz.import'
    _description = 'Import Accounting Winbiz'

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
                 In order to import your 'Winbiz Salaires' .xml \
                 file you must complete the following requirements : \
                <ul>
                <li> The accounts, analytical accounts used in the Cresus\
                 file must be previously created into Odoo  </li>
                <li> The date of the entry will determine the period used\
                 in Odoo, so please ensure the period is created already. </li>
                </ul>'''))

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
            self.write({'state': 'done',
                        'report': _("Lines imported"),
                        'imported_move_ids': result['ids']})
        else:
            self.write({'report': self.format_messages(result['messages']),
                        'state': 'error'})

    @api.multi
    def _standardise_data(self, data):
        """ This function split one line of the XML into multiple lines.
        Winbiz just writes one line per move.
        """
        new_openerp_data = []
        cp = self.env.user.company_id
        company_partner = cp.partner_id.name
        standard_dict = dict(izip_longest(self.HEAD_ODOO, []))
        previous_date = False
        for action_winbiz, elem_winbiz in data:
            # Contruct dict with date
            winbiz_item = {}
            for subelem in elem_winbiz.getchildren():
                winbiz_item.update({subelem.tag: subelem.text})
            for amount_type in ['lnmntent', 'lnmntsal']:
                default_value = standard_dict.copy()
                # We compute company part first after the employee
                decimal_amount = float(winbiz_item[amount_type])
                if (not previous_date) or \
                        previous_date != winbiz_item['st_date1']:
                    default_value.update({'date': winbiz_item['st_date1'],
                                          'ref': _('Payslip'),
                                          'journal_id': self.journal_id.name,
                                          'period_id': self.period_id.code
                                          })
                    previous_date = winbiz_item['st_date1']
                else:
                    default_value.update({'date': None,
                                          'ref': None,
                                          'journal_id': None,
                                          'period_id': None})
                if decimal_amount < 0:
                    default_value.update({'line_id/credit':
                                          abs(decimal_amount),
                                          'line_id/debit': 0.0,
                                          'line_id/account_id':
                                          winbiz_item['lcaccount']})
                else:
                    default_value.update({'line_id/debit': abs(decimal_amount),
                                          'line_id/credit': 0.0,
                                          'line_id/account_id':
                                          winbiz_item['lcaccount']})
                analytic_code = None
                analytic_code = winbiz_item['lcanaccount']
                default_value.update({'line_id/partner_id': company_partner,
                                      'line_id/name': _('Payslip'),
                                      'line_id/analytic_account_id':
                                      analytic_code})
                new_openerp_data.append(default_value)
        return new_openerp_data

    @api.multi
    def _load_data(self, data):
        """Function that does the load of parsed CSV file.

        It will log exception and susccess into the report fields.

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
        struct_xml = etree.iterparse(StringIO(
            self.file.decode('base64')), tag="c_liste_text")
        new_data = self._standardise_data(struct_xml)
        return self._load_data(new_data)
