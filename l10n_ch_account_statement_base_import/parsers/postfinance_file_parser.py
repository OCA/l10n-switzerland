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
from wand.image import Image
import logging

from openerp import fields

from .camt import PFCamtParser
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
        self.tar_source = data_file
        self.data_file = self._get_content_from_stream(data_file)
        self.attachments = None
        self.is_camt = None
        self.camt_parser = PFCamtParser()
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
            self.file_name = splitext(xmls[0])[0]
            return tar_file.extractfile(xmls[0]).read()
        except TarError:
            return data_file

    def _get_attachments_from_stream(self, data_file):
        """Retrieve attachment from tar file.
        Return a dict containing all attachments ready to be saved
        in Odoo.

        The key is the name of file without extension
        The value the PNG content encoded in base64

        :param data_file: raw statement file sent to odoo (not in b64)
        :type data_file: basestring subclass

        :return: Return a dict containing all attachments ready
        to be saved in Odoo.
        """
        pf_file = StringIO(data_file)
        pf_file.seek(0)
        try:
            attachments = {}
            tar_file = TarFile.open(fileobj=pf_file, mode="r:gz")
            accepted_formats = ['.tiff', '.png', '.jpeg', '.jpg']
            for file_name in tar_file.getnames():
                accepted = reduce(lambda x, y: x or y, [
                    file_name.endswith(format) for format in accepted_formats
                ])
                if accepted:
                    key = splitext(file_name)[0]
                    img_data = tar_file.extractfile(file_name).read()
                    if file_name.endswith('.tiff'):
                        # Convert to png for viewing the image in Odoo
                        with Image(blob=img_data) as img:
                            img.format = 'png'
                            img_data = img.make_blob()
                    attachments[key] = img_data.encode('base64')
            return attachments
        except TarError:
            return {}

    def file_is_known(self):
        """Predicate the tells if the parser can parse the data file

        :return: True if file is supported
        :rtype: bool
        """
        try:
            pf_xml = re.search(r'\<IC\b', self.data_file)
            if pf_xml is None:
                camt_xml = re.search('<GrpHdr>', self.data_file)
                if camt_xml is None:
                    return False
                self.is_camt = True
            return True
        except:
            return False

    def _parse_account_number(self, tree):
        """Parse file account number using xml tree
        :param tree: lxml element tree instance
        :type tree: :py:class:`lxml.etree.element.Element`

        :return: the file account number
        :rtype: string
        """
        account_number = None
        if self.is_camt:
            ns = tree.tag[1:tree.tag.index("}")]    # namespace
            account_node = tree.xpath(
                '//ns:Stmt/ns:Acct/ns:Id/ns:IBAN/text()',
                namespaces={'ns': ns})
        else:
            account_node = tree.xpath('//SG2/FII/C078/D_3194/text()')
        if account_node and len(account_node) == 1:
            account_number = account_node[0]
        return account_number

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
            raise ValueError(
                'Many currencies found for postfinance statement')
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

            res['name'] = "\n".join(transaction.xpath(
                "FTX/C108/D_4440/text()"))
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
            res['ref'] = uid if uid else desc
            res['account_number'] = None
            res['note'] = None
            res['partner_name'] = None
            transactions.append(res)
        return transactions

    def _parse_attachments(self, tree):
        """Parse file statement to get wich attachment to use
        :param tree: lxml element tree instance
        :type tree: :py:class:`lxml.etree.element.Element`

        :return: a list of attachment tuple (name, content)
        :rtype: list
        """
        attachments = [('Statement File', self.tar_source.encode('base64'))]
        if self.is_camt and self.is_tar:
            ns = tree.tag[1:tree.tag.index("}")]    # namespace
            transaction_nodes = tree.xpath(
                '//ns:Stmt/ns:Ntry/ns:AcctSvcrRef/text()',
                namespaces={'ns': ns})
            for transaction in transaction_nodes:
                att_name = self.file_name + '-' + transaction
                # Attachment files are limited to 87 char names
                att = self.attachments.get(att_name[:87])
                if att:
                    attachments.append((transaction, att))
        elif self.is_tar:
            transaction_nodes = tree.xpath("//SG6")
            for transaction in transaction_nodes:
                desc = '/'
                if transaction.xpath(".//@Value='ZZZ'"):
                    desc = transaction.xpath("RFF/C506/D_1154/text()")[1]
                att = self.attachments.get(desc)
                if att:
                    uid = [x.text for x in transaction.iter()
                           if (x.prefix == 'PF' and x.tag.endswith('D_4754'))]
                    uid = uid[0] if uid else desc
                    attachments.append((uid, att))
        return attachments

    def _parse_statement_date(self, tree):
        """Parse file statement date from tree
        :param tree: lxml element tree instance
        :type tree: :py:class:`lxml.etree.element.Element`

        :return: A date usable by Odoo in write or create dict
        :rtype: string
        """
        if self.is_camt:
            ns = tree.tag[1:tree.tag.index("}")]    # namespace
            date = tree.xpath(
                '//ns:GrpHdr/ns:CreDtTm/text()',
                namespaces={'ns': ns})
            if date:
                return date[0][:10]
        else:
            date = tree.xpath('//DTM/D_2380/@Desc="Date"')
            if date:
                formatted_date = date[0][:4] + '-' + date[0][4:6] + '-' + \
                    date[0][6:]
                return formatted_date
        return fields.Date.today()

    def _parse(self):
        """
        Launch the parsing through The XML file. It sets the various
        property of the class from the parse result.
        This implementation expect one XML file to represents one statement
        """
        if self.is_camt:
            tree = etree.fromstring(self.data_file)
            self.statements += self.camt_parser.parse(self.data_file)
            if self.statements:
                self.statements[0]['attachments'] = self._parse_attachments(
                    tree)
        else:
            tree = etree.fromstring(self.data_file)
            self.currency_code = self._parse_currency_code(tree)
            statement = {}
            balance_start, balance_stop = self._parse_statement_balance(tree)
            statement['balance_start'] = balance_start
            statement['balance_end_real'] = balance_stop
            statement['date'] = self._parse_statement_date(tree)
            statement['attachments'] = self._parse_attachments(tree)
            statement['transactions'] = self._parse_transactions(tree)
            self.statements.append(statement)
        self.account_number = self._parse_account_number(tree)
        return True
