# -*- coding: utf-8 -*-
# © 2017 Leonardo Franja (Opennet Sarl)
# Copyright (c) 2017-TODAY Open-Net Ltd.

"""
Set the existings salary rules as non-updatable
"""


def migrate(cr, version):
    if not version:
        return

    query = ("UPDATE hr_salary_rule "
             "SET amount_python_compute="
             "'result = contract.wage*payslip.working_rate/100' "
             "WHERE code='BASIC'")
    cr.execute(query)
