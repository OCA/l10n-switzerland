To use this module:

- Start workflow by call the url /ebill/subscribe. This allows the user
  to subscribe to e-billing with PostFinance by entering their mail.
- The user will receive an email from PostFinance with a code to confirm
  the subscription. User gets redirected to the url /ebill/validate
  where he can enter the code received by mail.
- Once the code is validated, the subscription is confirmed and the
  success page is shown.
