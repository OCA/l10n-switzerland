# Copyright 2015 Nicolas Bessi Camptocamp SA
# Copyright 2017-2019 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from PIL import Image
from os.path import splitext
from tarfile import TarFile, TarError
from lxml import etree
from xml.etree import ElementTree
from io import BytesIO, StringIO
from base64 import b64encode

from odoo import models

_logger = logging.getLogger(__name__)


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

        if statements and getattr(self, 'attachments', False):
            statements[0]['attachments'] = self._parse_attachments()

        return currency, account_number, statements

    def parse_transaction_details(self, ns, node, transaction):
        """Add file_reference to find attached image"""
        # add file_ref to link image to bank statement line
        self.add_value_from_node(
            ns, node, './ns:Refs//ns:Prtry/ns:Ref', transaction, 'file_ref')
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
        if self.is_tar:
            self.attachments = self._get_attachments_from_stream(data_file)

    def _get_content_from_stream(self):
        """Source file can be a raw or tar file. We try to guess the
        file type and return valid file content

        :return: uncompressed file content
        :rtype: string
        """
        # https://hg.python.org/cpython/file/6969bac411fa/Lib/tarfile.py#l2605
        self.is_tar = False
        if isinstance(self.tar_source, str):
            try:
                # If raw string
                ElementTree.fromstring(self.tar_source)
                return self.tar_source
            except ElementTree.ParseError:
                pf_file = StringIO(self.tar_source)
        else:
            pf_file = BytesIO(self.tar_source)
        try:
            pf_file.seek(0)
            with TarFile.open(fileobj=pf_file, mode="r:gz") as tar_file:
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
        pf_file = BytesIO(data_file)
        pf_file.seek(0)
        try:
            attachments = {}
            tar_file = TarFile.open(fileobj=pf_file, mode="r:gz")
            accepted_formats = ['.png', '.jpeg', '.jpg', '.tiff']
            for file_name in tar_file.getnames():
                if True in [file_name.endswith(f) for f in accepted_formats]:
                    key = splitext(file_name)[0]
                    img_data = tar_file.extractfile(file_name).read()
                    if file_name.endswith('.tiff'):
                        # Convert string containing data to tiff image
                        image = Image.open(BytesIO(img_data))

                        # Convert to png for viewing the image in Odoo
                        with BytesIO() as png_image:
                            image.save(png_image, format='PNG')
                            img_data = png_image.getvalue()
                    attachments[key] = b64encode(img_data)
            return attachments
        except TarError:
            return {}

    def _parse_attachments(self):
        """Parse file statement to get wich attachment to use
        :return: a list of attachment tuple (name, content)
        :rtype: list
        """
        attachments = [('Statement File', b64encode(self.tar_source))]
        if self.is_tar:
            # Extract XML tree
            try:
                tree = etree.fromstring(
                    self.data_file, parser=etree.XMLParser(recover=True))
            except etree.XMLSyntaxError:
                return attachments
            ns = tree.tag[1:tree.tag.index("}")]    # namespace
            transaction_nodes = tree.xpath(
                '//ns:Stmt//ns:Prtry/ns:Ref/text()',
                namespaces={'ns': ns})
            for transaction in transaction_nodes:
                att_name = self.file_name + '-' + transaction[:23]
                att = self.attachments.get(att_name)
                if att:
                    attachments.append((transaction, att))
        return attachments
