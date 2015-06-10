# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, David Wulliamoz
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
import datetime
import re
from os.path import splitext
from tarfile import TarFile, TarError
from cStringIO import StringIO
from lxml import etree
import logging

from openerp import fields

from .base_parser import BaseSwissParser

_logger = logging.getLogger(__name__)


class XMLPFParser(BaseSwissParser):
    """
    Parser for XML Postfinance Statements (can be wrapped in a tar.gz file)
    """

    _ftype = 'postfinance'

    def __init__(self, data_file):
        """Constructor
        Try to uncompress the file if possible
        """
        super(XMLPFParser, self).__init__(data_file)
        self.is_tar = None
        self.data_file = self._get_content_from_stream(data_file)
        self.attachments = None
        if self.is_tar:
            self.attachments = self._get_attachments_from_stream(data_file)

    def _get_content_from_stream(self, data_file):
        """Source file can be a raw or tar file. We try to guess the
        file type and return valid file content

        :retrun: uncompressed file content
        :rtype: string
        """
        # https://hg.python.org/cpython/file/6969bac411fa/Lib/tarfile.py#l2605
        pf_file = StringIO(data_file)
        pf_file.seek(0)
        try:
            # Taken from original code it seem we only want to
            # parse first XML file. TO BE CONFIRMED
            tar_file = TarFile.open(fileobj=pf_file, mode="r:gz")
            xmls = [tar_content
                    for tar_content in tar_file.getnames()
                    if tar_content.endswith('.xml')]
            self.is_tar = True
            return tar_file.extractfile(xmls[0]).read()
        except TarError:
            return data_file

    def _get_attachments_from_stream(self, data_file):
        """Retrive attachment from tar file.
        Return a dict containing all attachment ready to be saved
        in Odoo.

        The key is the name of file without extention
        The value the PNG content encoded in base64

        :param data_file: raw statement file sent to openerp (not in b64)
        :type data_file: basestring subclass

        :return: Return a dict containing all attachment ready
        to be saved in Odoo.
        """
        pf_file = StringIO(data_file)
        pf_file.seek(0)
        try:
            attachments = {}
            tar_file = TarFile.open(fileobj=pf_file, mode="r:gz")
            for file_name in tar_file.getnames():
                if file_name.endswith('.png'):
                    key = splitext(file_name)[0]
                    png_content = tar_file.extractfile(file_name).read()
                    attachments[key] = png_content.encode('base64')
            return attachments
        except TarError:
            return {}

    def ftype(self):
        """Gives the type of file we want to import

        :return: imported file type
        :rtype: string
        """
        return super(XMLPFParser, self).ftype()

    def get_currency(self):
        """Returns the ISO currency code of the parsed file

        :return: The ISO currency code of the parsed file eg: CHF
        :rtype: string
        """
        return super(XMLPFParser, self).get_currency()

    def get_account_number(self):
        """Return the account_number related to parsed file

        :return: The account number of the parsed file
        :rtype: string
        """
        return super(XMLPFParser, self).get_account_number()

    def get_statements(self):
        """Return the list of bank statement dict.
         Bank statements data: list of dict containing
            (optional items marked by o) :
            - 'name': string (e.g: '000000123')
            - 'date': date (e.g: 2013-06-26)
            -o 'balance_start': float (e.g: 8368.56)
            -o 'balance_end_real': float (e.g: 8888.88)
            - 'transactions': list of dict containing :
                - 'name': string
                   (e.g: 'KBC-INVESTERINGSKREDIET 787-5562831-01')
                - 'date': date
                - 'amount': float
                - 'unique_import_id': string
                -o 'account_number': string
                    Will be used to find/create the res.partner.bank in odoo
                -o 'note': string
                -o 'partner_name': string
                -o 'ref': string

        :return: a list of statement
        :rtype: list
        """
        return super(XMLPFParser, self).get_statements()

    def file_is_known(self):
        """Predicate the tells if the parser can parse the data file

        :return: True if file is supported
        :rtype: bool
        """
        try:
            return re.search(r'\<IC\b', self.data_file) is not None
        except:
            return False

    def _parse_account_number(self, tree):
        """Parse file account number using xml tree
        :param tree: lxml element tree instance
        :type tree: :py:class:`lxml.etree.element.Element`

        :return: the file account number
        :rtype: string
        """
        account_node = tree.xpath('//SG2/FII/C078/D_3194/text()')
        if not account_node:
            return
        if len(account_node) != 1:
            raise ValueError('Many account found for postfinance statement')
        return account_node[0]

    def _parse_currency_code(self, tree):
        """Parse file currency ISO code using xml tree
        :param tree: lxml element tree instance
        :type tree: :py:class:`lxml.etree.element.Element`

        :return: the currency ISO code of the file eg: CHF
        :rtype: string
        """
        currency_node = tree.xpath('//SG2/FII/C078/D_6345/@Value')
        if not currency_node:
            return
        if len(currency_node) != 1:
            raise ValueError('Many currency found for postfinance statement')
        return currency_node[0]

    def _parse_statement_balance(self, tree):
        """Parse file start and end balance
        :param tree: lxml element tree instance
        :type tree: :py:class:`lxml.etree.element.Element`

        :return: the file start and end balance
        :rtype: tuple (start, end) balances
        """
        balance_start = balance_end = False
        balance_nodes = tree.xpath("//SG5/MOA/C516")
        for move in balance_nodes:
            if move.xpath(".//@Value='315'"):
                balance_start = float(move.xpath("./D_5004/text()")[0])

            if move.xpath(".//@Value='343'"):
                balance_end = float(move.xpath("./D_5004/text()")[0])
        return balance_start, balance_end

    def _parse_transactions(self, tree):
        """Parse bank statement lines from file
        list of dict containing :
            - 'name': string (e.g: 'KBC-INVESTERINGSKREDIET 787-5562831-01')
            - 'date': date
            - 'amount': float
            - 'unique_import_id': string
            -o 'account_number': string
                Will be used to find/create the res.partner.bank in odoo
            -o 'note': string
            -o 'partner_name': string
            -o 'ref': string

        :param tree: lxml element tree instance
        :type tree: :py:class:`lxml.etree.element.Element`

        :return: a list of transactions
        :rtype: list
        """
        transactions = []
        transaction_nodes = tree.xpath("//SG6")
        for transaction in transaction_nodes:
            if not transaction.xpath(".//@Value='TGT'"):
                continue
            res = {}
            desc = '/'
            date = datetime.date.today()
            if transaction.xpath(".//@Value='TGT'"):
                transaction_date_text = transaction.xpath(
                    "DTM/C507/D_2380/text()"
                )
                if transaction_date_text:
                    date = datetime.datetime.strptime(
                        transaction_date_text[0], "%Y%m%d").date()
            res['date'] = fields.Date.to_string(date)

            if transaction.xpath(".//@Value='ZZZ'"):
                desc = transaction.xpath("RFF/C506/D_1154/text()")[1]

            res['ref'] = "\n".join(transaction.xpath("FTX/C108/D_4440/text()"))
            amount = float(transaction.xpath("MOA/C516/D_5004/text()")[0])
            if transaction.xpath("MOA/C516/D_5025/@Value='211'"):
                amount *= -1
            res['amount'] = amount
            # We have an issue with XPATH and namespace here because of
            # faulty definition on a deprecated URL
            uid = [x.text for x in transaction.iter()
                   if (x.prefix == 'PF' and x.tag.endswith('D_4754'))]
            uid = uid[0] if uid else None
            res['unique_import_id'] = uid
            res['name'] = uid if uid else desc
            res['account_number'] = None
            res['note'] = None
            res['partner_name'] = None
            transactions.append(res)
        return transactions

    def _parse_attachments(self, tree):
        """Parse file statement to get wich attachement to use
        :param tree: lxml element tree instance
        :type tree: :py:class:`lxml.etree.element.Element`

        :return: a list of attachement tuple (name, content)
        :rtype: list
        """
        attachments = []
        transaction_nodes = tree.xpath("//SG6")
        for transaction in transaction_nodes:
            desc = '/'
            if transaction.xpath(".//@Value='ZZZ'"):
                desc = transaction.xpath("RFF/C506/D_1154/text()")[1]
            att = self.attachments.get(desc)
            if att:
                attachments.append((desc, att))
        return attachments

    def _parse_statement_date(self, tree):
        """Parse file statement date from tree
        :param tree: lxml element tree instance
        :type tree: :py:class:`lxml.etree.element.Element`

        :return: A date usable by Odoo in write or create dict
        :rtype: string
        """
        # I was not able to find a correct segment group to extract the date
        date = datetime.date.today()
        return fields.Date.to_string(date)

    def _parse(self):
        """
        Launch the parsing through The XML file. It sets the various
        property of the class from the parse result.
        This implementation expect one XML file to represents one statement
        """
        tree = etree.fromstring(self.data_file)
        self.currency_code = self._parse_currency_code(tree)
        self.account_number = self._parse_account_number(tree)
        statement = {}
        balance_start, balance_stop = self._parse_statement_balance(tree)
        statement['balance_start'] = balance_start
        statement['balance_end_real'] = balance_stop
        statement['date'] = self._parse_statement_date(tree)
        statement['attachments'] = self._parse_attachments(tree)
        statement['transactions'] = self._parse_transactions(tree)
        self.statements.append(statement)
        return True
