-- disable alipay2 payment provider
UPDATE payment_provider
   SET alipay2_appid = NULL,
       alipay2_merchant_no = NULL,
       alipay2_app_private_key = NULL,
       alipay2_public_key = NULL;
