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
import logging
from os.path import splitext
from tarfile import TarFile, TarError
from cStringIO import StringIO
from lxml import etree

from openerp import models

_logger = logging.getLogger(__name__)


try:
    from wand.image import Image
    wand = True
except ImportError:
    _logger.warning('Please install Wand (sudo pip wand) for Postfinance '
                    'bank statement import supporting tiff attachments.')
    wand = None


class XMLPFParser(models.AbstractModel):
    """
    Parser for XML Postfinance Statements (can be wrapped in a tar.gz file)
    """
    _inherit = 'account.bank.statement.import.camt.parser'

    def parse(self, data_file):
        """
        Handle Postfinance images of payment slips.
        """
        self._check_postfinance_attachments(data_file)

        currency, account_number, statements = super(XMLPFParser, self).parse(
            self.data_file)

        if statements and self.attachments:
            statements[0]['attachments'] = self._parse_attachments()

        return currency, account_number, statements

    def parse_transaction_details(self, ns, node, transaction):
        """Add file_reference to find attached image"""
        # add file_ref to link image to bank statement line
        self.add_value_from_node(
            ns, node, './ns:Refs/ns:AcctSvcrRef', transaction, 'file_ref')
        super(XMLPFParser, self).parse_transaction_details(
            ns, node, transaction)

    def parse_statement(self, ns, node):
        """
        Find currency if not found with base parser
        """
        result = super(XMLPFParser, self).parse_statement(ns, node)
        if not result.get('currency'):
            currency_node = node.xpath(
                '//ns:Bal[1]/ns:Amt/@Ccy', namespaces={'ns': ns})
            if currency_node and len(currency_node) == 1:
                result['currency'] = currency_node[0]
        return result

    def _check_postfinance_attachments(self, data_file):
        """
        Initialize parser and check that data_file can be parsed.
        :param data_file: file data
        """
        self.tar_source = data_file
        self.data_file = self._get_content_from_stream()
        self.attachments = self._get_attachments_from_stream(data_file)

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
            accepted_formats = ['.png', '.jpeg', '.jpg']
            if wand:
                accepted_formats.append('.tiff')
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

    def _parse_attachments(self):
        """Parse file statement to get wich attachment to use
        :return: a list of attachment tuple (name, content)
        :rtype: list
        """
        attachments = [('Statement File', self.tar_source.encode('base64'))]
        if self.is_tar:
            # Extract XML tree
            try:
                tree = etree.fromstring(
                    self.data_file, parser=etree.XMLParser(recover=True))
            except etree.XMLSyntaxError:
                return attachments
            ns = tree.tag[1:tree.tag.index("}")]    # namespace
            transaction_nodes = tree.xpath(
                '//ns:Stmt/ns:Ntry/ns:AcctSvcrRef/text()',
                namespaces={'ns': ns})
            for transaction in transaction_nodes:
                att_name = self.file_name + '-' + transaction[:23]
                att = self.attachments.get(att_name)
                if att:
                    attachments.append((transaction, att))
        return attachments
