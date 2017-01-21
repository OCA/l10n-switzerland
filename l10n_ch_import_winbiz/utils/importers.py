# -*- coding: utf-8 -*-
# Copyright 2016 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
import tempfile
import base64
import logging

import xml.etree.ElementTree as ET
from babel import Locale
from abc import ABCMeta, abstractmethod

_logger = logging.getLogger(__name__)

try:
    from xlrd import open_workbook, xldate_as_tuple
except ImportError:
    _logger.debug('Can not `from xlrd import open_workbook, xldate_as_tuple`.')


class BaseImporter:
    __metaclass__ = ABCMeta

    def parse_input(self, content):
        """Parse the data as received from the web form and split it into rows.

           :param content: base64-encoded string
           :returns: list(dict(name: value))
        """
        # We use tempfile in order to avoid memory error with large files
        with tempfile.TemporaryFile() as src:
            src.write(content)
            with tempfile.NamedTemporaryFile() as decoded:
                src.seek(0)
                base64.decode(src, decoded)
                decoded.seek(0)
                res = self._parse_input_decoded(decoded)
        res.sort(key=lambda e: int(e[u'numéro']))
        return res

    @abstractmethod
    def _parse_input_decoded(self, decoded):
        """Receive the base64-decoded data and split it into rows.

           :param decoded: file object
           :returns: list(dict(name: value))
        """

    @abstractmethod
    def parse_date(self, date):
        """Parse a date in the data.

           :param date: value
           :returns: datetime.date
        """


class XLSImporter(BaseImporter):
    def __init__(self):
        self.wb = None

    def _parse_input_decoded(self, decoded):
        self.wb = open_workbook(decoded.name, encoding_override='cp1252')
        sheet = self.wb.sheet_by_index(0)
        vals = (lambda n: [c.value for c in sheet.row(n)])
        head = vals(0)
        return [dict(zip(head, vals(i))) for i in xrange(1, sheet.nrows)]

    def parse_date(self, date):
        """Parse a date coming from Excel.

           :param date: cell value
           :returns: datetime.date
        """
        if isinstance(date, basestring):
            d, m, y = date.split('-')
            d = int(d)
            mapping = Locale('en').months['format']['abbreviated']
            mapping = dict(zip(mapping.values(), mapping.keys()))
            m = mapping[m]
            y = 2000 + int(y)
            return datetime.datetime(y, m, d)
        else:
            return datetime.datetime(*xldate_as_tuple(date, self.wb.datemode))


class XMLImporter(BaseImporter):
    def _parse_input_decoded(self, decoded):
        tree = ET.parse(decoded.name)
        rows = tree.getroot()
        if len(rows[0].attrib):
            return [row.attrib for row in rows]
        else:
            return [{el.tag: el.text or '' for el in row} for row in rows]

    def parse_date(self, date):
        return datetime.datetime.strptime(date, '%Y-%m-%d')


def getImporter(file_format):
    if file_format == 'xls':
        return XLSImporter()
    elif file_format == 'xml':
        return XMLImporter()
