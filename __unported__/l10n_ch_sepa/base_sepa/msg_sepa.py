# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
#    Copyright 2011 Camptocamp SA
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

from lxml import etree
from StringIO import StringIO

from openerp.osv import orm
from openerp.tools.translate import _


SEPA_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'


class MsgSEPA(object):

    _xsd_path = None
    _xml_data = None

    def __init__(self, xsd_path=None):
        '''If no xsd is defined, we consider that we will use the basid
        iso20022 XSD file

        '''
        self._xsd_path = xsd_path

    def _is_xsd_valid(self):
        '''Check the validity of XML data with an XML Schema
        Return True if it is valid

        Raise an error if no XML data have been defined
        Raise an error if XSD file specified is not found'''
        if not self._xml_data:
            raise orm.except_orm(_('Error'), _('No XML data found'))

        try:
            f_xsd = open(self._xsd_path)
        except:
            raise orm.except_orm(_('Error'), _('No XSD file found'))

        parser = etree.XMLParser()
        xmlschema_doc = etree.parse(f_xsd)
        xmlschema = etree.XMLSchema(xmlschema_doc)

        xml_data = etree.parse(StringIO(self._xml_data.encode('utf-8')),
                               parser=parser)

        try:
            xmlschema.assertValid(xml_data)
        except etree.DocumentInvalid, e:
            raise orm.except_orm(
                _('XML is not Valid !'),
                _('The document validation has raised following errors: \n%s')
                % e.message)

        return True


class MsgSEPAFactory(object):
    """This class is a factory that creates SEPA message in order to allow
    redefinition of those message to match with different country
    implementations

    """
    _register = {}

    @classmethod
    def register_class(cls, key, class_name, **args):
        cls._register[key] = (class_name, args)

    @classmethod
    def get_instance(cls, key, **args):
        (class_name, cargs) = cls._register[key]
        args = dict(cargs.items() + args.items())
        return class_name(**args)

    @classmethod
    def has_instance(cls, key):
        return key in cls._register

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
