update res_better_zip set active = False where id in (select res_id from ir_model_data where model = 'res.better.zip' and name like 'npa_%');
