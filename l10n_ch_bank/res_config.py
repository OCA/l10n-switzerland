# b-*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2010 brain-tec AG (http://www.brain-tec.ch)
#    All Right Reserved
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

from openerp.osv import osv
import os
from openerp.tools.convert import convert_xml_import
from openerp.tools import misc
import tempfile


class base_config_settings(osv.osv_memory):
    _inherit = 'account.config.settings'
    
    def update_banks(self, cr, uid, ids, context=None):
        # first update field 'noupdate' in ir.model.data for all entries related to model 'res.bank' and module 'l10n_ch' to 'False'
        sql = "update ir_model_data set noupdate = False where model = 'res.bank' and module = 'l10n_ch'"
        cr.execute(sql)
         
        # create new xml file in temp folder and set noupdate Flag to False in order to update all the entries when the customer wants to update all the banks
        # set all bank's inactive which have an entry in ir_model_data -> this means they were created by xml
        sql = "update res_bank set active = False where id in (select res_id from  ir_model_data where model = 'res.bank' and module = 'l10n_ch')"
        cr.execute(sql)
        
        filename = 'bank.xml'
        noupdate = False
        pathname = os.path.join('l10n_ch_bank', filename)
        fp = misc.file_open(pathname)
        try:
            # read current xml
            xml_string = fp.read()
            # create new xml to change noupdate 1 to 0
            new_bank_xml_path = tempfile.mkstemp('.xml')[1]
            new_bank_xml = open(new_bank_xml_path, 'w+')
            new_bank_xml.write(xml_string.replace('data noupdate="1"', 'data noupdate="0"'))
            new_bank_xml.close()
            fp = misc.file_open(new_bank_xml_path)
            convert_xml_import(cr, 'l10n_ch_bank', fp, {}, 'update', noupdate, False)
            #delete new_bank.xml file after all is done
            new_bank_xml.close()
            os.unlink(new_bank_xml_path)
        finally:
            fp.close()
        cr.commit()

        # set field 'noupdate' in ir.model.data for all entries related to model 'res.bank' and module 'l10n_ch' back to 'True'
        sql = "update ir_model_data set noupdate = True where model = 'res.bank' and module = 'l10n_ch'"
        cr.execute(sql)
        return True
