# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2013 Camptocamp SA (http://www.camptocamp.com)
#
# Author: Romain Deheele (Camptocamp)
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
##############################################################################

import pooler
import tools

from mako import exceptions
from openerp.osv.osv import except_osv
from openerp.tools.translate import _
from openerp import addons
from openerp.addons.report_webkit import webkit_report
from openerp.addons.report_webkit.webkit_report import mako_template
from openerp.addons.report_webkit.report_helper import WebKitHelper

class MultiBvrWebKitParser(webkit_report.WebKitParser):
 
    def create_single_pdf(self, cursor, uid, ids, data, report_xml, context=None):
        self.pool = pooler.get_pool(cursor.dbname)
        target_obj = 'account.move.line'
        move_line_obj = self.pool.get(target_obj)    
        account_obj = self.pool.get('account.account')        
        invoice_obj = self.pool.get('account.invoice')
        inv = invoice_obj.browse(cursor, uid, ids[0],context)
        tier_account_id = account_obj.search(cursor, uid, [('type','in',['receivable','payable'])])
        move_lines = move_line_obj.search(cursor, uid, [('move_id','=',inv.move_id.id),('account_id','in',tier_account_id)])
        #outputs
        context['active_model'] = self.table = target_obj
        context['active_ids'] = ids = move_lines
        return super(MultiBvrWebKitParser,self).create_single_pdf(cursor, uid, ids, data, report_xml, context)
        

