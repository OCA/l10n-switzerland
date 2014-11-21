# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright David Wulliamoz SA
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.tools.translate import _
from openerp.osv.osv import except_osv
import tempfile
import datetime
import tarfile
from account_statement_base_import.parser.parser \
    import BankStatementImportParser

from lxml import etree

import logging

_logger = logging.getLogger(__name__)


class XMLPFParser(BankStatementImportParser):
    """
    Parser for XML Postfinance Statements (can be wrapped in a tar.gz file)
    """

    def __init__(self, parse_name, ftype='xml', **kwargs):
        """
        :param char: parse_name: The name of the parser
        :param char: ftype: extension of the file (could be xml)
        """

        super(XMLPFParser, self).__init__(parse_name, **kwargs)

        if ftype in ('xml', 'gz'):
            self.ftype = ftype
        else:
            raise except_osv(_('User Error'),
                             _('Invalid file type %s. Please use xml or gz') %
                             ftype)

    @classmethod
    def parser_for(cls, parser_name):
        """
        Used by the new_bank_statement_parser class factory. Return true if
        the providen name is generic_csvxls_so
        """
        return parser_name == 'pf_xmlparser'

    def _custom_format(self, *args, **kwargs):
        """
        Extract the XML statement if the given file is a tar gz file.
        """
        if self.ftype == 'gz':
            pf_file = tempfile.NamedTemporaryFile()
            pf_file.write(self.filebuffer)
            # We ensure that cursor is at beginning of file
            pf_file.seek(0)

            tfile = tarfile.open(fileobj=pf_file, mode="r:gz")
            tfile_xml = [filename
                         for filename in tfile.getnames()
                         if filename.endswith('.xml')]

            self.filebuffer = tfile.extractfile(tfile_xml[0]).read()

        return True

    def _pre(self, *args, **kwargs):
        """
        No pre-treatment needed for this parser.
        """
        return True

    def _parse(self, *args, **kwargs):
        """
        Launch the parsing through .xml
        """
        reader = etree.fromstring(self.filebuffer)
        r = reader.xpath("//SG5/MOA/C516")
        for move in r:
            if move.xpath(".//@Value='315'"):
                self.balance_start = float(move.xpath("./D_5004/text()")[0])

            if move.xpath(".//@Value='343'"):
                self.balance_end = float(move.xpath("./D_5004/text()")[0])

        r = reader.xpath("//SG6")
        res = []
        for move in r:
            if move.xpath(".//@Value='TGT'"):
                transaction_date = move.xpath("DTM/C507/D_2380/text()")
                if transaction_date:
                    date = datetime.datetime.strptime(
                        transaction_date[0], "%Y%m%d").date()
                if move.xpath(".//@Value='ZZZ'"):
                    ref = move.xpath("RFF/C506/D_1154/text()")[1]
                else:
                    ref = "/"
                lib = "\n".join(move.xpath("FTX/C108/D_4440/text()"))
                amount = float(move.xpath("MOA/C516/D_5004/text()")[0])
                if move.xpath("MOA/C516/D_5025/@Value='211'"):
                    amount *= -1

                line_res = {'ref': ref, 'lib': lib, 'amount': amount}
                if date:
                    line_res.update({'date': date.strftime(
                        "%Y-%m-%d")})
                res.append(line_res)

        self.result_row_list = res
        return True

    def _validate(self, *args, **kwargs):
        """
        Nothing to validate.
        """
        return True

    def _post(self, *args, **kwargs):
        """
        No special conversion needed.
        """
        return True

    def get_st_line_vals(self, line, *args, **kwargs):
        """
        This method must return a dict of vals that can be passed to create
        method of statement line in order to record it.
            :param:  line: a dict of vals that represent a line of
                           result_row_list
            :return: dict of values to give to the create method of
                     statement line,
        """
        res = {
            'name': line.get('lib', line.get('ref', '/')),
            'date': line.get('date', datetime.date.today()),
            'amount': line.get('amount', 0.0),
            'ref': line.get('ref', '/'),
            'label': line.get('lib', ''),
        }

        return res
