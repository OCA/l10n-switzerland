* Build a script to update the `res.bank.csv` file to ease maintenance.

  Currently it's built manually, like this:

  #. Download the Excel file from `SIX Interbank Clearing <http://www.six-interbank-clearing.com/en/home/bank-master-data/download-bc-bank-master.html>`_.

  #. Generate the `id` column like this: `bank_{iid}_{branch_id}`.

  #. Generate the `country` column with values `Switzerland`.

  #. Map the following columns to the corresponding fields:

     * "IID" -> `clearing`
     * "Branch ID" -> `branch_code`
     * "Short Name" -> `code`
     * "Bank/Institution Name" -> `name`
     * "Domicile Address" -> `street`
     * "Postal Address" -> `street2`
     * "Phone" -> `phone`
     * "Zip Code" -> `zip`
     * "Place" -> `city`
     * "BIC" -> `bic`
