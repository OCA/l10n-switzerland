# -*- coding: utf-8 -*-
# Copyright 2015 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from xlrd import open_workbook, xldate_as_tuple
import tempfile
from openerp import models, fields, api, exceptions
from datetime import datetime

FILE_EXPECTED_COLUMNS = [
  u'ecr_numero',
  u'numéro',
  u'ecr_noline',
  u'date',
  u'pièce',
  u'libellé',
  u'cpt_débit',
  u'cpt_crédit',
  u'montant',
  u'journal',
  u'ecr_monnai',
  u'ecr_cours',
  u'ecr_monmnt',
  u'ecr_monqte',
  u'ecr_tvatyp',
  u'ecr_tvatx',
  u'ecr_tvamnt',
  u'ecr_tvabn',
  u'ecr_tvadc',
  u'ecr_tvapt',
  u'ecr_tvaarr',
  u'ecr_tvamod',
  u'ecr_ana',
  u'ecr_diver1',
  u'ecr_verrou',
  u'ecr_ref1',
  u'ecr_ref2',
  u'ecr_ref1dc',
  u'ecr_ref2dc',
  u'ecr_type_d',
  u'ecr_type_c',
  u'ecr_mon_op',
  u'ecr_diver2',
  u'ecr_vtnum',
  u'ecr_vtcode',
  u'ecr_ext']

class AccountWinbizImport(models.TransientModel):
    _name = 'account.winbiz.import'
    _description = 'Import Accounting Winbiz'
    _rec_name = 'state'

    company_id = fields.Many2one('res.company', 'Company', invisible=True)
    report = fields.Text('Report', readonly=True)
    journal_id = fields.Many2one('account.journal', 'Journal', required=True)
    state = fields.Selection(selection=[
        ('draft', "Draft"),
        ('done', "Done"),
        ('error', "Error")],
        readonly=True,
        default='draft')
    file = fields.Binary('File', required=True)
    imported_move_ids = fields.Many2many(
            'account.move', 'import_cresus_move_rel',
            string='Imported moves')

    help_html = fields.Html('Import help', readonly=True,
            default='''
                 In order to import your 'Winbiz Salaires' .xml \
                         file you must complete the following requirements : \
                         <ul>
                <li> The accounts, analytical accounts used in the Cresus\
                        file must be previously created into Odoo  </li>
                </ul>''')

    ODOO_MOVE_ARGS = {'ref', 'date', 'journal_id'}

    @staticmethod
    def make_move(lines, **kwargs):
        # assert set(kwargs.keys()) == self.ODOO_MOVE_ARGS
        kwargs.update({'line_ids': [(0, 0, ln) for ln in lines]})
        return kwargs

    ODOO_LINE_ARGS = {'account_id', 'partner_id', 'name',
            'tax_line_id', 'analytic_account_id'}

    @staticmethod
    def make_line(debit=0.0, credit=0.0, **kwargs):
        # assert set(kwargs.keys()) == self.ODOO_LINE_ARGS
        kwargs.update({'debit': debit, 'credit': credit})
        return kwargs

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

    def _parse_xls(self):
        """Parse stored Excel file.

        Manage base 64 decoding.

        :param imp_id: current importer id
        :returns: generator

        """
        # We use tempfile in order to avoid memory error with large files
        with tempfile.TemporaryFile() as src:
            content = self.file
            src.write(content)
            with tempfile.NamedTemporaryFile() as decoded:
                src.seek(0)
                base64.decode(src, decoded)
                decoded.seek(0)
                wb = open_workbook(decoded.name, encoding_override='cp1252')
                self.wb = wb
                sheet = wb.sheet_by_index(0)
                for n, tag in enumerate(FILE_EXPECTED_COLUMNS):
                    assert sheet.row(0)[n].value == tag
                for i in xrange(1, sheet.nrows):
                    yield {tag: sheet.row(i)[n].value
                           for n, tag in enumerate(FILE_EXPECTED_COLUMNS)}

    def _parse_date(self, date):
        """Parse a date coming from Excel.

           :param date: cell value
           :returns: datetime
        """
        dt = datetime(*xldate_as_tuple(date, self.wb.datemode))
        return dt

    @api.multi
    def _standardise_data(self, data):
        """
        This function split one line of the spreadsheet into multiple lines.
        Winbiz just writes one line per move.
        """

        journal_id = self.journal_id.id
        incomplete = None
        previous_pce = None
        previous_date = None
        lines = []
        for self.index, winbiz_item in enumerate(data, 1):
            if previous_pce is not None and previous_pce != winbiz_item[u'pièce']:
                if incomplete and incomplete['debit'] and incomplete['credit']:
                    if incomplete['debit'] < incomplete['credit']:
                        incomplete['credit'] -= incomplete['debit']
                        incomplete['debit'] = 0
                    else:
                        incomplete['debit'] -= incomplete['credit']
                        incomplete['credit'] = 0
                yield self.make_move(
                        lines,
                        date=previous_date,
                        ref=previous_pce,
                        journal_id=journal_id)
                lines = []
                incomplete = None
            previous_pce = winbiz_item[u'pièce']
            previous_date = self._parse_date(winbiz_item[u'date'])

            amount = float(winbiz_item[u'montant'])
            if amount == 0:
                continue

            recto_line = verso_line = None
            if winbiz_item[u'cpt_débit'] != 'Multiple':
                account = self._find_account(winbiz_item[u'cpt_débit'])
                if incomplete is not None and incomplete['account_id'] == account.id:
                    incomplete['debit'] += amount
                else:
                    recto_line = self.make_line(
                            debit=amount,
                            account_id=account.id,
                            partner_id=False,
                            name=winbiz_item[u'libellé'],
                            tax_line_id=None,
                            analytic_account_id=None)
                    lines.append(recto_line)

            if winbiz_item[u'cpt_crédit'] != 'Multiple':
                account = self._find_account(winbiz_item[u'cpt_crédit'])
                if incomplete is not None and incomplete['account_id'] == account.id:
                    incomplete['credit'] += amount
                else:
                    verso_line = self.make_line(
                            credit=amount,
                            account_id=account.id,
                            partner_id=False,
                            name=winbiz_item[u'libellé'],
                            tax_line_id=None,
                            analytic_account_id=None)
                    lines.append(verso_line)

            if winbiz_item[u'cpt_débit'] == 'Multiple':
                assert incomplete is None
                incomplete = verso_line
            if winbiz_item[u'cpt_crédit'] == 'Multiple':
                assert incomplete is None
                incomplete = recto_line

        yield self.make_move(
                lines,
                date=previous_date,
                ref=previous_pce,
                journal_id=journal_id)

    @api.multi
    def _import_file(self):
        self.index = None
        move_obj = self.env['account.move']
        data = self._parse_xls()
        data = self._standardise_data(data)
        self.imported_move_ids = [move_obj.create(mv).id for mv in data]

    @api.multi
    def import_file(self):
        try:
            self._import_file()
        except Exception as exc:
            self.env.cr.rollback()
            self.write({
                'state': 'error',
                'report': 'Error (at row %s):\n%r' % (self.index, exc)})
            return {'name': 'Import Move lines',
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.winbiz.import',
                    'res_id': self.id,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new'}
        self.state = 'done'
        # show the resulting moves in main content area
        return {'domain': str([('id', 'in', self.imported_move_ids.ids)]),
                'name': 'Imported Journal Entries',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'view_id': False,
                'type': 'ir.actions.act_window'}
