# -*- coding: utf-8 -*-
# Copyright 2015 Camptocamp SA
# Copyright 2016 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import csv
import tempfile
from odoo import models, fields, api, exceptions
from odoo.tools.translate import _
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

    def prepare_move(self, lines, date, ref, journal_id):
        move = {}
        move['date'] = date
        move['ref'] = ref
        move['journal_id'] = journal_id
        move['line_ids'] = [(0, 0, ln) for ln in lines]
        return move

    def prepare_line(self, name, debit_amount, credit_amount, account_code,
                     cresus_tax_code, analytic_account_code, tax_ids):
        account_obj = self.env['account.account']
        tax_obj = self.env['account.tax']
        analytic_account_obj = self.env['account.analytic.account']

        line = {}
        line['name'] = name
        line['debit'] = debit_amount
        line['credit'] = credit_amount

        account = account_obj.search([('code', '=', account_code)], limit=1)
        if not account:
            raise exceptions.MissingError(
                _("No account with code %s") % account_code)
        line['account_id'] = account.id

        if cresus_tax_code:
            tax = tax_obj.search([
                ('tax_cresus_mapping', '=', cresus_tax_code),
                ('price_include', '=', True)], limit=1)
            line['tax_line_id'] = tax.id
        if analytic_account_code:
            analytic_account = analytic_account_obj.search([
                ('code', '=', analytic_account_code)], limit=1)
            line['analytic_account_id'] = analytic_account.id

        if tax_ids:
            line['tax_ids'] = [(4, id, 0) for id in tax_ids]
        return line

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
                    raise exceptions.ValidationError(
                        _('CSV file is malformed\n'
                          'Please choose the correct separator\n'
                          'the error detail is:\n'
                          '%r') % error)
                for line in data:
                    line['date'] = self._parse_date(line['date'])
                    yield line

    def _parse_date(self, date_string):
        """Parse a date coming from Crésus and put it in the format used by Odoo.

           Both 01.01.70 and 01.01.1970 have been sighted in Crésus' output.

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
                _("Can't parse date '%s'") % date_string)
        return fields.Date.to_string(dt)

    @api.multi
    def _standardise_data(self, data):
        """ split accounting lines where needed

            Crésus writes one csv line per move when there are just two lines
            (take some money from one account and put all of it in another),
            and uses ellipses in more complex cases. What matters is the pce
            label, which is the same on all lines of a move.
        """
        journal_id = self.journal_id.id
        previous_pce = None
        previous_date = None
        previous_tax_id = None
        lines = []
        for self.index, line_cresus in enumerate(data, 1):
            if previous_pce is not None and previous_pce != line_cresus['pce']:
                yield self.prepare_move(
                    lines,
                    date=previous_date,
                    ref=previous_pce,
                    journal_id=journal_id)
                lines = []
            previous_pce = line_cresus['pce']
            previous_date = line_cresus['date']

            from babel.numbers import parse_decimal
            recto_amount = float(parse_decimal(line_cresus['amount'],
                                               locale='de_CH'))
            verso_amount = 0.0
            if recto_amount < 0:
                recto_amount, verso_amount = 0.0, -recto_amount

            tax_ids = [previous_tax_id] if previous_tax_id is not None else []
            previous_tax_id = None
            if line_cresus['debit'] != '...':
                line = self.prepare_line(
                    name=line_cresus['ref'],
                    debit_amount=recto_amount,
                    credit_amount=verso_amount,
                    account_code=line_cresus['debit'],
                    cresus_tax_code=line_cresus['typtvat'],
                    analytic_account_code=line_cresus['analytic_account'],
                    tax_ids=tax_ids)
                lines.append(line)
                if 'tax_line_id' in line:
                    previous_tax_id = line['tax_line_id']

            if line_cresus['credit'] != '...':
                line = self.prepare_line(
                    name=line_cresus['ref'],
                    debit_amount=verso_amount,
                    credit_amount=recto_amount,
                    account_code=line_cresus['credit'],
                    cresus_tax_code=line_cresus['typtvat'],
                    analytic_account_code=line_cresus['analytic_account'],
                    tax_ids=tax_ids)
                lines.append(line)
                if 'tax_line_id' in line:
                    previous_tax_id = line['tax_line_id']

        yield self.prepare_move(
            lines,
            date=line_cresus['date'],
            ref=previous_pce,
            journal_id=journal_id)

    @api.multi
    def _import_file(self):
        self.index = 0
        data = self._parse_csv()
        data = self._standardise_data(data)
        for mv in data:
            self.with_context(dont_create_taxes=True) \
                .write({'imported_move_ids': [(0, False, mv)]})

    @api.multi
    def import_file(self):
        try:
            self._import_file()
        except Exception as exc:
            self.env.cr.rollback()
            self.write({
                'state': 'error',
                'report': 'Error (at row %s):\n%s' % (self.index, exc)})
            return {'name': _('Accounting Crésus Import'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.cresus.import',
                    'res_id': self.id,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new'}
        self.state = 'done'
        # show the resulting moves in main content area
        return {'domain': str([('id', 'in', self.imported_move_ids.ids)]),
                'name': _('Imported Journal Entries'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'view_id': False,
                'type': 'ir.actions.act_window'}
