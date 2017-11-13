# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Nicolas Bessi. Copyright Camptocamp SA
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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
#
##############################################################################
{
    'name' : 'l10_ch_zip',
    'description' : 'Better zip management data for CH',
    'version' : '0.1',
    'depends' : [
                 'better_zip',
                 ],
    'author' : 'Camptocamp',
    'description': """better zip data for Switzerland""",
    'website': 'http://www.camptocamp.com',
    'init_xml': [],
    'update_xml': [
                    'l10n_ch_better_zip.xml',
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}