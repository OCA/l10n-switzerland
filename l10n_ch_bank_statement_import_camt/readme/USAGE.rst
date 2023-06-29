Journals can be defined as "QR IBAN for import" which modify the way the import will behave.
If this is marked it will search for a bank account with a l10n_ch_qr_iban corresponding to the second IBAN available in the camt (Ntry/NtryRef xml tag).
This allow to have a bank account set on two different journals and use the QRR swiss functionality to import on his own specific journal the referenced transactions.
