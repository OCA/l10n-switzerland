# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


def _is_l10n_ch_qr_iban(account_ref):
    """Returns if the account_ref is a QR IBAN

    A QR IBAN contains an IID QR.
    An IID QR is between 30000 and 31999
    It starts at the 5th character
    eg: CH21 3080 8001 2345 6782 7
    where 30808 is the IID QR
    """
    account_ref = account_ref.replace(" ", "")
    return (
        account_ref.startswith("CH")
        and account_ref[4:9] >= "30000"
        and account_ref[4:9] <= "31999"
    )


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    def is_isr_issuer(self):
        """Supplier will provide ISR reference numbers in two cases:

        - postal account number starting by 01 or 03
        - QR-IBAN
        """
        # acc_type can be bank for isrb
        if self.acc_type in ["bank", "postal"] and self.l10n_ch_postal:
            return self.l10n_ch_postal[:2] in ["01", "03"]
        return self.acc_type == "iban" and _is_l10n_ch_qr_iban(self.acc_number)
