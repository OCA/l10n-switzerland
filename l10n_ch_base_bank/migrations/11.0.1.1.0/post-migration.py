# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


def reference_type_bvr_to_isr(cr):
    """Change BVR to ISR in reference_type field"""
    cr.execute("""
        UPDATE account_invoice SET reference_type='isr'
        WHERE reference_type = 'bvr';
        """)


@openupgrade.migrate()
def migrate(env, version):
    reference_type_bvr_to_isr(env.cr)
