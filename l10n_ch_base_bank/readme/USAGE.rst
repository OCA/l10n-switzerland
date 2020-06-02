In partner bank account the type will be discovered automatically.

* For IBAN accounts fill account number with IBAN.
  * if the IBAN is an IBAN from PostFinance it will fill the Postal account number
* For Postal accounts:
  * fill the account number with a postal account number 9 digits format (e.g. 10-8060-7).
  * or fill the "Swiss postal account" with a postal account number 9 digits format (e.g. 10-8060-7).

Entering a postal number of 9 digits will auto-complete the bank with PostFinance. (You might create it if you haven't installed `l10n_ch_bank`)

* For ISR subscription numbers (postal account starting with 01 or 03):
  * fill the account number with a postal account number 9 digits format (e.g. 01-23456-1).
  * or fill the "Swiss postal account" with a postal account number 9 digits format (e.g. 01-23456-1).

It will automatically change the content of account number by adding "ISR" and the partner name to avoid
duplicates with partner using the same ISR subscription number owned by a bank (ISR-B).
