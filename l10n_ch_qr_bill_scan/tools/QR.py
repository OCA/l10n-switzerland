import re

# Positions
SPC = 0
VERSION = 1
IBAN = 3
CREDITOR = 4  # Till 10
CREDITOR_NAME = 5
AMOUNT = 18
CURRENCY = 19
REF = 28
MSG = 29
EPD = 30
BILL_INFO = 31

ADR_LEN = 7

valid_re = re.compile(r"SPC\n(.*\n){29}EPD")
