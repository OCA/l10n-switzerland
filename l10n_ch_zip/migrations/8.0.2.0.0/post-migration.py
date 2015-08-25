# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Mathias Neef
#    Copyright 2015 copadoMEDIA UG
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

"""
In previews versions the states in Switzerland are created within this module.
Now they are seperated in extra module l10n_ch_states. This modul now depends
on l10n_ch_states.
"""

import logging

logger = logging.getLogger('upgrade')


def migrate(cr, version):
    if not version:
        logger.info("No migration necsessary for l10n_ch_zip")
        return

    logger.info("Migrating l10n_ch_zip from version %s", version)

    cr.execute("SELECT name, res_id "
               "FROM ir_model_data "
               "WHERE module = 'l10n_ch_zip' "
               "AND model = 'res.country.state';")

    for name, res_id in cr.fetchall():

        old_state = res_id

        cr.execute("SELECT res_id "
                   "FROM ir_model_data "
                   "WHERE name = %s "
                   "AND module = 'l10n_ch_states';", (name,))

        new_state = cr.fetchone()

        logger.info(
            "Updating state_id from id %s to id %s",
            old_state, new_state
        )

        cr.execute("UPDATE res_partner "
                   "SET state_id = %s"
                   "WHERE state_id = %s", (new_state, old_state))

        cr.execute("UPDATE res_better_zip "
                   "SET state_id = %s "
                   "WHERE state_id = %s;", (new_state, old_state))

        cr.execute("DELETE FROM res_country_state "
                   "WHERE id = %s;", (old_state,))

    logger.info(
        "Delete old states from ir_model_data"
    )

    cr.execute("DELETE FROM ir_model_data "
               "WHERE module = 'l10n_ch_zip' "
               "AND model = 'res.country.state'")
