# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2011 Camptocamp SA (http://www.camptocamp.com)
# All Right Reserved
#
# Author : Yannick Vaucher (Camptocamp)
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import os

from l10n_ch_sepa.base_sepa.msg_sepa import MsgSEPAFactory
from l10n_ch_sepa.base_sepa.pain_001 import Pain001

_xsd_path = os.path.join('l10n_ch_sepa', 'l10n_ch', 'xsd',
                         'pain.001.001.03.ch.02.xsd')
_tmpl_dirs = [os.path.join('l10n_ch_sepa', 'l10n_ch', 'template')]
_tmpl_name = 'pain.001.001.03.ch.02.xml.mako'


MsgSEPAFactory.register_class('pain.001.ch', Pain001,
                              xsd_path=_xsd_path,
                              tmpl_dirs=_tmpl_dirs,
                              tmpl_name=_tmpl_name)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
