# -*- coding: utf-8 -*-
###############################################################################
#
#   Authors: David Wulliamoz <dwulliamoz@compassion.ch>
#            Emanuel Cino <ecino@compassion.ch>
#   Copyright 2013-2014 Compassion CH
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import logging
import datetime
import tempfile
import csv
from account_statement_base_import.parser.file_parser import FileParser

_logger = logging.getLogger(__name__)

""" Overwrite UnicodeDictReader so that delimiter is always ';' """
def UnicodeDictReader(utf8_data, **kwargs):
    csv.register_dialect('ubs', delimiter=';', quoting=csv.QUOTE_NONE)
    csv_reader = csv.DictReader(utf8_data, dialect='ubs', **kwargs)
    for row in csv_reader:
        yield dict([(key, unicode(value, 'utf-8')) for key, value in row.iteritems()])

def float_or_zero(val):
    """ Conversion function used to manage
    empty string into float usecase"""
    val = val.replace("'", "")
    return float(val) if val else 0.0

def format_date(val):
    return datetime.datetime.strptime(val, "%d.%m.%Y")


class UBSFileParser(FileParser):

    def __init__(self, parse_name, ftype='csv', **kwargs):
        super(UBSFileParser,self).__init__(parse_name, ftype=ftype, **kwargs)
        self.conversion_dict = {
            "Date de comptabilisation": format_date,
            "Description 1": unicode,
            "Description 2": unicode,
            "Description 3": unicode,
            "Débit": float_or_zero,
            "Crédit": float_or_zero,
        }
        self.keys_to_validate = self.conversion_dict.keys()

    @classmethod
    def parser_for(cls, parser_name):
        """
        Used by the new_bank_statement_parser class factory. Return true if
        the providen name is ubs_csvparser
        """
        return parser_name == 'ubs_csvparser'

    def _custom_format(self, *args, **kwargs):
        """
        The file format is in iso-8859-15, must be converted to utf-8 before parsing.
        """
        self.filebuffer = self.filebuffer.decode('iso-8859-15').encode('utf-8')
        return True

    def _pre(self, *args, **kwargs):
        """ Retrieve the starting and ending balance to be inserted in the bank statement. """
        split_file = self.filebuffer.splitlines()
        solde_line = split_file[-1]
        self.balance_end = float_or_zero(solde_line.split(";")[0])
        self.balance_start = float_or_zero(solde_line.split(";")[1])
        
        # Remove the balance line
        self.filebuffer = "\n".join(split_file[:-3])
        return True
        
    def get_st_line_vals(self, line, *args, **kwargs):
        """
        This method must return a dict of vals that can be passed to create
        method of statement line in order to record it. It is the responsibility
        of every parser to give this dict of vals, so each one can implement his
        own way of recording the lines.
            :param:  line: a dict of vals that represent a line of result_row_list
            :return: dict of values to give to the create method of statement line,
        """
        descriptions = [line.get("Description 1", '/'),line.get("Description 2", ''),line.get("Description 3", '')]
        label = ' '.join(filter(None,descriptions))
        amount = -line["Débit"] or line["Crédit"] or 0.0
        
        res = {
            'name': label,
            'date': line.get("Date de comptabilisation", datetime.datetime.now().date()),
            'amount': amount,
            'ref': '/',
            'label': label
        }
	
        return res
        
    def _parse_csv(self):
        """
        :return: list of dict from csv file (line/rows)
        """
        csv_file = tempfile.NamedTemporaryFile()
        csv_file.write(self.filebuffer)
        csv_file.flush()
        with open(csv_file.name, 'rU') as fobj:
            reader = UnicodeDictReader(fobj, fieldnames=self.fieldnames)
            return list(reader)
