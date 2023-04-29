# -*- coding: utf-8 -*-
"""
Created on Fri Nov  5 22:49:41 2021

@author: marcu
"""
import sys
sys.path.append("D:\\Users\\Marcus\\Documents\\R Documents\\Coding\\Python\\Packages")

import ofx_parser as ofxp
from mh_logging import log_class
import constants as c

log_class = log_class(c.LOG_LEVEL)

class Transactions:
    _dict_keys = ['fit_id', 'type', 'amount', 'payment_type',
                  'counter_party', 'reference', 'date_posted']
    @log_class
    def __init__(self, ofx = None):
        """ Open a connection to either an existing OFX class, or create a new
        instance from a filepath """
        if ofx is None:
            self.ofx = None
        elif isinstance(ofx, ofxp.OFX):
            self.ofx = ofx
        elif isinstance(ofx, str):
            self.ofx = ofxp.OFX(filename = ofx)
        else:
            raise TypeError

        self.transactions = None
        self.count = None

    @classmethod
    def from_ofx(cls, ofx):
        if not isinstance(ofx, ofxp.OFX):
            raise TypeError("Argument must be an instance of the OFX class")
        return Transactions(ofx)

    @classmethod
    def from_path(cls, path):
        if not isinstance(path, str):
            raise TypeError("Argument must be string filepath to .ofx file")
        return Transactions(path)

    @classmethod
    def from_transaction(cls, transaction):
        if not isinstance(transaction, ofxp.Transaction):
            raise TypeError("Argument must be an instance of the "
                            "Transaction class")
        tclass = Transactions()
        tclass.transactions = [tclass._get_transaction_dict(transaction)]
        tclass.count = 1
        return tclass

    @classmethod
    def from_dict(cls, transaction):
        if not isinstance(transaction, dict):
            raise TypeError("Argument must be a dictionary")

        tclass = Transactions()

        if not set(transaction.keys()) == set(tclass._dict_keys):
            raise TypeError(
                "Dictionary missing required keys, or has unneeded keys. Keys "
                "'fit_id', 'type', 'amount', 'payment_type', 'counter_party', "
                "'reference' must be present.")

        tclass.transactions = [transaction]
        tclass.count = 1
        return tclass

    @classmethod
    def from_dict_list(cls, transaction):
        if not isinstance(transaction, list):
            raise TypeError("Argument must be a list")

        tclass = Transactions()

        tclass.transactions = transaction
        tclass.count = len(transaction)
        return tclass

    @classmethod
    def from_transaction_list(cls, transaction):
        if not isinstance(transaction, list):
            raise TypeError("Argument must be a list")

        tclass = Transactions()

        tclass.transactions = [
            tclass._get_transaction_dict(t) for t in transaction]
        tclass.count = len(tclass.transactions)

        return tclass

    @log_class
    def _get(self):
        self.transactions = [self._get_transaction_dict(t)
                             for t in self.ofx.get_transactions()]
        self.count = len(self.transactions)

    @log_class
    def get(self):
        if self.transactions is None:
            self._get()
        return self.transactions

    @log_class
    def _get_transaction_dict(self, transaction):
        tdict = {k: transaction.__dict__[k]
                 for k in self._dict_keys
                 }
        tdict['date_posted'] = transaction.date_posted.isoformat()
        return tdict

    def __iter__(self):
        """
        Allow iteration like "for n in Transactions".
        """
        if self.transactions is None:
            self._get()
        self._i = -1
        return self

    def __next__(self):
        if self._i < self.count - 1:
            self._i += 1
            return self.transactions[self._i]
        else:
            raise StopIteration