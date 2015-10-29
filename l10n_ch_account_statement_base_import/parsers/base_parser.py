# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2015 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from abc import ABCMeta, abstractmethod
import logging
from openerp import _, exceptions
_logger = logging.getLogger(__name__)


class BaseSwissParser(object):
    """Base parser class for every Swiss file format.
    It provides a base abstraction for every parser
    of swiss localisation"""
    __metaclass__ = ABCMeta
    _ftype = None

    def __init__(self, data_file):
        """Constructor
        :param data_file: the raw content of the file to be imported
        :type data_file: string
        """
        if not data_file:
            raise ValueError('File must not be empty')
        self.data_file = data_file
        self.currency_code = None
        self.account_number = None
        self.statements = []

    def ftype(self):
        """Gives the type of file we want to import
        This method is abstract, we want to ensure that developper aware of it.
        If the base behavior is enought the child implementation should consist
        in a simple call to super
        :return: imported file type
        :rtype: string
        """
        if not self._ftype:
            raise ValueError('No file type defined')
        return self._ftype

    def parse(self):
        """Parse the file the file to import"""
        try:
            return self._parse()
        except Exception as exc:
            _logger.exception(
                'Error when parsing {ftype} file'.format(ftype=self.ftype())
            )
            raise exceptions.Warning(
                _("The following problem occurred during {ftype} import. "
                  "The file might not be valid.\n\n {msg}").format(
                      ftype=self.ftype(), msg=exc.message)
            )

    @abstractmethod
    def file_is_known(self):
        """Predicate the tells if the parser can parse the data file
        This method is abstract

        :return: True if file is supported
        :rtype: bool
        """
        pass

    @abstractmethod
    def _parse(self):
        """Do the parsing process job
        This method is abstract
        """
        pass

    def get_currency(self):
        """Returns the ISO currency code of the parsed file
        This method is abstract, we want to ensure that developper aware of it.
        If the base behavior is enought the child implementation should consist
        in a simple call to super
        :return: The ISO currency code of the parsed file eg: CHF
        :rtype: string
        """
        return self.currency_code

    def get_account_number(self):
        """Return the account_number related to parsed file
        This method is abstract, we want to ensure that developper aware of it.
        If the base behavior is enought the child implementation should consist
        in a simple call to super
        :return: The account number of the parsed file
        :rtype: dict
        """

        return self.account_number

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
        This method is abstract

        :return: a list of statement
        :rtype: list
        """
        return self.statements
