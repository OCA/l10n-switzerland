# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, David Wulliamoz, Emanuel Cino
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
import re
from os.path import splitext
from tarfile import TarFile, TarError
from cStringIO import StringIO
from lxml import etree
from wand.image import Image
import logging

from openerp.addons.account_bank_statement_import_camt.camt import CamtParser


_logger = logging.getLogger(__name__)


class PFCamtParser(CamtParser):
    """Parser for camt bank statement files of PostFinance SA."""

    def parse_transaction_details(self, ns, node, transaction):
        """Change how reference is read."""
        # add file_ref to link image to bank statement line
        self.add_value_from_node(
            ns, node, './ns:Refs/ns:AcctSvcrRef', transaction, 'file_ref')
        super(PFCamtParser, self).parse_transaction_details(
            ns, node, transaction)


class XMLPFParser(object):
    """
    Parser for XML Postfinance Statements (can be wrapped in a tar.gz file)
    """

    def _parse(self, data_file):
        """
        Launch the parsing through The XML file. It sets the various
        property of the class from the parse result.
        This implementation expect one XML file to represents one statement
        """
        if not self._check_postfinance(data_file):
            raise ValueError('Not a valid Postfinance statement')

        tree = etree.fromstring(self.data_file)
        self.currency_code = self._parse_currency_code(tree)
        camt_parser = PFCamtParser()
        currency, account_number, statements = camt_parser.parse(
            self.data_file)
        if statements:
            statements[0]['attachments'] = self._parse_attachments(
                tree)
        return self.currency_code, account_number, statements

    def _check_postfinance(self, data_file):
        """
        Initialize parser and check that data_file can be parsed.
        :param data_file: file data
        :return: True/False
        """
        self.tar_source = data_file
        self.data_file = self._get_content_from_stream()
        if self.is_tar:
            self.attachments = self._get_attachments_from_stream(data_file)
        else:
            self.attachments = None
        camt_xml = re.search('<GrpHdr>', self.data_file) and re.search(
            '<AcctSvcrRef>', self.data_file)
        if camt_xml is None:
            return False
        return True

    def _get_content_from_stream(self):
        """Source file can be a raw or tar file. We try to guess the
        file type and return valid file content

        :return: uncompressed file content
        :rtype: string
        """
        # https://hg.python.org/cpython/file/6969bac411fa/Lib/tarfile.py#l2605
        self.is_tar = False
        pf_file = StringIO(self.tar_source)
        pf_file.seek(0)
        try:
            tar_file = TarFile.open(fileobj=pf_file, mode="r:gz")
            xmls = [tar_content
                    for tar_content in tar_file.getnames()
                    if tar_content.endswith('.xml')]
            self.is_tar = True
            self.file_name = splitext(xmls[0])[0]
            return tar_file.extractfile(xmls[0]).read()
        except TarError:
            return self.tar_source

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

    def _parse_currency_code(self, tree):
        """Parse file currency ISO code using xml tree
        :param tree: lxml element tree instance
        :type tree: :py:class:`lxml.etree.element.Element`

        :return: the currency ISO code of the file eg: CHF
        :rtype: string
        """
        ns = tree.tag[1:tree.tag.index("}")]  # namespace
        currency_node = tree.xpath(
            '//ns:Stmt/ns:Bal[1]/ns:Amt/@Ccy',
            namespaces={'ns': ns})
        if not currency_node:
            return
        if len(currency_node) != 1:
            raise ValueError(
                'Many currencies found for Postfinance statement')
        return currency_node[0]

    def _parse_attachments(self, tree):
        """Parse file statement to get wich attachment to use
        :param tree: lxml element tree instance
        :type tree: :py:class:`lxml.etree.element.Element`

        :return: a list of attachment tuple (name, content)
        :rtype: list
        """
        attachments = [('Statement File', self.tar_source.encode('base64'))]
        if self.is_tar:
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
        return attachments
