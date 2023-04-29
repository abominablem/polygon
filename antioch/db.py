# -*- coding: utf-8 -*-
"""
Created on Sat Apr 29 18:01:06 2023

@author: marcu
"""

import sys
sys.path.append("D:\\Users\\Marcus\\Documents\\R Documents\\Coding\\Python\\Packages")

import ofx_parser as ofxp
import sqlite_tablecon as sqt
from transactions import Transactions
from mh_logging import log_class
import constants as c

log_class = log_class(c.LOG_LEVEL)

antioch_db = sqt.MultiConnection(
    db = c.DB_PATH,
    tables = ['transactions',
              'transaction_detail',
              'accounts',
              'classifications'],
    debug = c.DEBUG
    )


class AntiochException(Exception):
    pass

class TransactionExistsError(AntiochException):
    """ Raised when transaction already exists in database """
    def __init__(self, fit_id):
        super().__init__("Transaction %s already exists in database" % fit_id)


class AntiochDatabaseHandler:
    def __init__(self):
        self.transactions = TransactionHandler()

class AccountsHandler:
    def __init__(self):
        self.db = antioch_db.accounts

    def get_id(self, **kwargs):
        result = self.db.filter(kwargs, "id")
        return result["id"]

class ClassificationsHandler:
    def __init__(self):
        self.db = antioch_db.classifications

    def get_id(self, **kwargs):
        result = self.db.filter(kwargs, "id")
        return result["id"]

class TransactionHandler:
    def __init__(self):
        self.db = antioch_db.transactions
        self.db_detail = antioch_db.transaction_detail

    def add(self, transaction, account, skip_existing = True):
        if isinstance(transaction, ofxp.Transaction):
            transaction = Transactions.from_transaction(transaction)
        elif isinstance(transaction, Transactions):
            pass
        elif isinstance(transaction, ofxp.OFX):
            transaction = Transactions.from_ofx(transaction)
        elif isinstance(transaction, dict):
            transaction = Transactions.from_dict(transaction)
        elif isinstance(transaction, list):
            if isinstance(transaction[0], dict):
                transaction = Transactions.from_dict_list(transaction)
            elif isinstance(transaction[0], ofxp.Transaction):
                transaction = Transactions.from_transaction_list(transaction)
            else:
                raise ValueError("Unsupported transaction type")
        else:
            raise ValueError("Unsupported transaction type")

        for t_dict in transaction:
            fit_id = t_dict["fit_id"]
            # Check if fit_id already exists
            if self.exists(fit_id):
                if skip_existing:
                    continue
                else:
                    raise TransactionExistsError(fit_id)

            # First create a row in the transactions table
            trans_cols = {key: t_dict[key] for key in [
                'fit_id', 'date_posted', 'type', 'counter_party', 'reference',
                'payment_type', 'amount']}
            self.db.insert(account = account, **trans_cols)

            # Add a delta row to the transactions detail table. This
            # captures the amount of the transaction but no details yet about
            # the classification/decription
            self.add_detail(
                fit_id = fit_id, amount = t_dict["amount"],
                delta_flag = 1)

    def add_detail(self, fit_id, amount, delta_flag, **kwargs):
        # Get the auto-generated transaction id for this fit_id
        tid = self.get_id(fit_id)
        # Exactly one id should be returned
        if len(tid) != 1:
            raise ValueError

        tid = tid[0]

        kwargs.setdefault('classification_id', c.CLASSIFICATION_ID_UNCLASSIFIED)

        self.db_detail.insert(transaction_id = tid, amount = float(amount),
                              delta_flag = delta_flag, **kwargs)
        self.db_detail.insert(transaction_id = tid, amount = float(amount),
                              delta_flag = delta_flag, **kwargs)

        self._update_delta(tid)

    def _update_delta(self, transaction_id):
        """ Update the amount of the delta row, adding a row if it doesn't
        exist and removing excess rows """
        ids = self._get_ids(transaction_id, delta_flag = 1)

        # No delta row yet - add one
        if len(ids) == 0:
            self._add_delta(transaction_id, set_delta = False)

        # Too many delta rows - combine them
        elif len(ids) > 1:
            self._clean_delta(transaction_id, ids = ids)

        # Update the now single delta row with the delta amount
        self._set_delta(transaction_id)

    def _add_delta(self, transaction_id, set_delta = True):
        """ Add a dummy delta row for a given transaction. This must be updated
        subsequently with the correct delta amount if set_delta is not True"""
        self.db_detail.insert(
            transaction_id = transaction_id, amount = 0,
            classification_id = c.CLASSIFICATION_ID_UNCLASSIFIED,
            delta_flag = 1
            )
        if set_delta:
            self._set_delta(transaction_id)

    def _clean_delta(self, transaction_id, ids = None):
        """ Detect and combine multiple delta rows """
        if not ids is None:
            ids = sorted(ids)
            ids = [str(row_id) for row_id in ids]
            sql = "DELETE FROM %s WHERE id IN (%s)" % (
                self.db_detail.table,
                ", ".join(ids[1:])
                )
            self.db_detail.execute(sql, select = False)
        else:
            ids = self._get_ids(transaction_id, delta_flag = 1)
            self._clean_delta(transaction_id, ids)

    def _get_delta(self, transaction_id):
        """ Recalculate the delta flag amount based on the transaction amount
        and total amount against non-delta rows """
        # Get the total amount currently against non-delta rows
        sql = """
            SELECT COALESCE((SELECT [amount] FROM %s WHERE id = %s), 0) -
            COALESCE((SELECT SUM([amount]) FROM %s WHERE [transaction_id] = %s
             AND [delta_flag] = 0), 0) """ % (self.db.table, transaction_id,
            self.db_detail.table, transaction_id)
        delta_amount = float(self.db_detail.execute(sql, select = True)[0][0])
        return delta_amount

    def _set_delta(self, transaction_id, delta_amount = None):
        """ Set delta amount for a given transaction """
        if delta_amount is None:
            delta_amount = self._get_delta(transaction_id)

        self.db_detail.update({"transaction_id": transaction_id},
                              amount = delta_amount)

    def _get_ids(self, transaction_id, delta_flag = None):
        """ Return list of row IDs against a transaction """
        if delta_flag is None:
            result = self.db_detail.filter(
                {"transaction_id": transaction_id}, ["id"])
        else:
            result = self.db_detail.filter(
                {"transaction_id": transaction_id, "delta_flag": delta_flag},
                ["id"]
                )
        return result['id']


    def import_ofx(self, ofx, account, skip_existing = True):
        if isinstance(ofx, str):
            ofx = ofxp.OFX(filename = ofx)
        transactions = Transactions.from_ofx(ofx)
        self.add(transactions, account, skip_existing)

    def exists(self, fit_id):
        """ Return True if given fit_id exists in transactions database, and
        False otherwise """
        result = self.db.filter({"fit_id": fit_id}, "fit_id")
        return len(result["fit_id"]) != 0

    def get_id(self, fit_id):
        result = self.db.filter({"fit_id": fit_id}, "id")
        return result["id"]


if __name__ == "__main__":
    filename = r"D:\Users\Marcus\Downloads\TransactionHistory (2).ofx"
    # tf = Transactions.from_path(filename)
    # t = tf.get()

    th = TransactionHandler()

    th.import_ofx(filename, account = 1)