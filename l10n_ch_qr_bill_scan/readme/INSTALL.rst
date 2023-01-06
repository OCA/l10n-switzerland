This module depends on `account_invoice_import` which is located in `edi` and has dependencies on `community-data-files`.
So the repositories `edi` and `community-data-files` must be present on the system.

Optionally you can also import Vendor bills directly from a PDF.
To enable this feature those additional dependencies must be
installed on your Odoo server:

    pip install pyzbar,numpy,pdf2image,opencv-python-headless

If you are looking to generate QR-bill, this feature is already available
in Odoo in the Switzerland localization module (`l10n_ch`).
