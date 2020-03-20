from odoo.exceptions import except_orm


class NoTransactionsError(except_orm):
    def __init__(self, message, obj):
        self.name = message
        self.message = message
        self.object = obj


class NoPaymentReturnError(except_orm):
    def __init__(self, message):
        self.name = message
        self.message = message


class FileAlreadyImported(except_orm):
    def __init__(self, message, obj):
        self.name = message
        self.message = message
        self.object = obj


class ErrorOccurred(except_orm):
    def __init__(self, message, obj):
        self.name = message
        self.message = message
        self.object = obj
