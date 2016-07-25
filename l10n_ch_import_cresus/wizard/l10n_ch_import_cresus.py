# -*- coding: utf-8 -*-
# Copyright 2015 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import csv
import tempfile
from openerp import models, fields, api, exceptions
from datetime import datetime


class AccountCresusImport(models.TransientModel):
    _name = 'account.cresus.import'
    _description = 'Export Accounting'

    company_id = fields.Many2one('res.company', 'Company',
                                 invisible=True)
    report = fields.Text(
        'Report',
        readonly=True
        )
    journal_id = fields.Many2one('account.journal', 'Journal',
                                 required=True)
    state = fields.Selection(selection=[('draft', "Draft"),
                                        ('done', "Done"),
                                        ('error', "Error")],
                             readonly=True,
                             default='draft')
    file = fields.Binary(
        'File',
        required=True)
    imported_move_ids = fields.Many2many(
        'account.move', 'import_cresus_move_rel',
        string='Imported moves')

    HEAD_CRESUS = ['date', 'debit', 'credit', 'pce',
                   'ref', 'amount', 'typtvat', 'currency_amount',
                   'analytic_account']

    ODOO_MOVE_ARGS = {'ref', 'date', 'journal_id'}

    @staticmethod
    def make_move(lines, **kwargs):
        # assert set(kwargs.keys()) == self.ODOO_MOVE_ARGS
        kwargs.update({'line_ids': [(0, 0, ln) for ln in lines]})
        return kwargs

    ODOO_LINE_ARGS = {'account_id', 'partner_id', 'name',
                      'tax_line_id', 'analytic_account_id'}

    @staticmethod
    def make_line(debit_amount, credit_amount, **kwargs):
        # assert set(kwargs.keys()) == self.ODOO_LINE_ARGS
        kwargs.update({'debit': debit_amount, 'credit': credit_amount})
        return kwargs

    def _parse_csv(self):
        """Parse stored CSV file.

        Manage base 64 decoding.

        :returns: generator

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
                try:
                    data = csv.DictReader(decoded, fieldnames=self.HEAD_CRESUS,
                                          delimiter=delimiter)
                except csv.Error as error:
                    raise exceptions.ValidationError('CSV file is malformed\n'
                                                     'Please choose the correct separator\n'
                                                     'the error detail is:\n'
                                                     '%r' % error)
                for line in data:
                    line['date'] = self._parse_date(line['date'])
                    yield line

    def _parse_date(self, date_string):
        """Parse a date coming from Cresus and put it in the format used by Odoo.

           Both 01.01.70 and 01.01.1970 have been sighted in Cresus' output.

           :param date_string: cresus data
           :returns: a date string
        """
        for format in ['%d.%m.%y', '%d.%m.%Y']:
            try:
                dt = datetime.strptime(date_string, format)
                break
            except ValueError:
                continue
        else:
            raise exceptions.ValidationError(
                "Can't parse date '%s'" % date_string)
        return fields.Date.to_string(dt)

    def _find_account(self, code):
        account_obj = self.env['account.account']
        account = account_obj.search([('code', '=', code)], limit=1)
        if not account:
            raise exceptions.MissingError("No account with code %s" % code)
        return account

    def _find_tax(self, typtvat, account):
        tax_obj = self.env['account.tax']
        if not typtvat or account.user_type_id.include_initial_balance:
            return tax_obj
        else:
            return tax_obj.search([('tax_cresus_mapping', '=', typtvat),
                                   ('price_include', '=', True)], limit=1)

    def _find_analytic_account(self, code, account):
        analytic_account_obj = self.env['account.analytic.account']
        if not code or account.user_type_id.include_initial_balance:
            return analytic_account_obj
        else:
            return analytic_account_obj.search([('code', '=', code)], limit=1)

    @api.multi
    def _standardise_data(self, data):
        """ split accounting lines where needed

            Cresus writes one csv line per move when there are just two lines
            (take some money from one account and put all of it in another),
            and uses ellipses in more complex cases. What matters is the pce
            label, which is the same on all lines of a move.
        """
        journal_id = self.journal_id.id
        previous_pce = None
        previous_date = None
        lines = []
        for self.index, line_cresus in enumerate(data, 1):
            if previous_pce is not None and previous_pce != line_cresus['pce']:
                yield self.make_move(
                    lines,
                    date=previous_date,
                    ref=previous_pce,
                    journal_id=journal_id)
                lines = []
            previous_pce = line_cresus['pce']
            previous_date = line_cresus['date']

            recto_amount = float(line_cresus['amount'].replace('\'', '')
                                                      .replace(' ', ''))
            verso_amount = 0.0
            if recto_amount < 0:
                recto_amount, verso_amount = 0.0, -recto_amount
            if line_cresus['debit'] != '...':
                account = self._find_account(line_cresus['debit'])
                tax = self._find_tax(line_cresus['typtvat'], account)
                analytic_account = self._find_analytic_account(
                    line_cresus['analytic_account'], account)
                lines.append(self.make_line(
                    recto_amount, verso_amount,
                    account_id=account.id,
                    partner_id=False,
                    name=line_cresus['ref'],
                    tax_line_id=tax.id,
                    analytic_account_id=analytic_account.id))

            if line_cresus['credit'] != '...':
                account = self._find_account(line_cresus['credit'])
                tax = self._find_tax(line_cresus['typtvat'], account)
                analytic_account = self._find_analytic_account(
                    line_cresus['analytic_account'], account)
                lines.append(self.make_line(
                    verso_amount, recto_amount,
                    account_id=account.id,
                    partner_id=False,
                    name=line_cresus['ref'],
                    tax_line_id=tax.id,
                    analytic_account_id=analytic_account.id))

        yield self.make_move(
            lines,
            date=line_cresus['date'],
            ref=previous_pce,
            journal_id=journal_id)

    @api.multi
    def _import_file(self):
        move_obj = self.env['account.move']
        data = self._parse_csv()
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
                'report': 'Error (at row %s):\n%s' % (self.index, exc)})
            return {'name': 'Import Move lines',
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.cresus.import',
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
