# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        """
        UPDATE ebill_postfinance_invoice_message
            SET payment_type = 'iban'
            WHERE payment_type = 'qr';
        UPDATE ebill_postfinance_invoice_message
            SET payment_type = 'esr'
        WHERE payment_type = 'isr';
        """
    )
