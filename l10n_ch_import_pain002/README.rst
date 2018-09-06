.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Switzerland import pain002 files
================================

This module allow you to import pain002 files. It will automatically cancel payment and reconciliation for
rejected payment.

** Features list :**
    * import pain002 files
    * parse pain002 files
    * unpost rejected payments
    * unreconcile rejected payments
    * remove payments lines from rejected payments
    * remove payment order there's no more payment line in it

Known issues / Roadmap
======================
If pmt is in return (use EndToEndId to identify the payment order payment.order.line.name)
    * do the same as rejected pain002
    * reconcile together payment out with the in
    * do this in the completion/reconcile process


Contributors
------------

* Marco Monzione
