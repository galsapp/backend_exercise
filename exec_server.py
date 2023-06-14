import threading
from datetime import datetime
from enum import Enum
from functools import partial

import time

import processor

from exec_db import Transaction_Table, Future_Transaction, bank_accounts, db, db_bank, tables, queries

from Transaction import Transaction


class Verbose(Enum):
    DEBUG = 1
    FULL = 2
    HIGH = 3
    MEDIUM = 4
    LOW = 5
    NONE = 6


# defining a decorator for logging
def add_log(func):
    """
    decorator function wrapper function and print before and after run function

    """

    def inner(*args, **kwargs):
        if isinstance(args[0], ExecManager):
            args[0]._add_log(
                f'Start {func.__name__} with args: {args}, kwargs: {kwargs}')

        # inside the wrapper function.
        ret = func(*args, **kwargs)
        if isinstance(args[0], ExecManager):
            args[0]._add_log(f'End   {func.__name__} return: {ret}')
        return ret

    return inner


class ExecManager:
    """
    The restAPI manager class

    """
    def __init__(self):

        # for logger
        self.log_verbosity = Verbose.DEBUG
        self.server_log = 'exec_log.txt'

        # connect db
        db.connect(reuse_if_open=True)
        db_bank.connect(reuse_if_open=True)

        # Add options to the tables
        for table in tables:
            for q in queries:
                sql_func = getattr(table, q)
                setattr(table, f"exec_{q}", partial(self._run_sql, sql_func))

        # Open thread for schedule tasks
        t_thread = threading.Thread(target=self._schedule_tasks)
        t_thread.start()

    def _schedule_tasks(self):
        """
        This function make a schedule tasks:
        1. Every 7 A.M. preform a download of a daily report.
        2. Check if needed to make a new transaction from the 'Future_Transaction' table.
        """
        can_run_daily_method = True
        while True:
            time.sleep(10)

            # Get the current time
            current_time = datetime.now().time()

            # Check if it is 7 AM - to preform daily method
            if current_time.hour == 7 and can_run_daily_method:
                processor.download_report()
                can_run_daily_method = False
            else:
                can_run_daily_method = True

            rows = Future_Transaction.select().order_by(Future_Transaction.time_for_transact.asc()).execute()
            for row in rows:
                # we don't have a real trans to make at this time
                if row.time_for_transact > time.time():
                    break

                # we have to make a trans from the future table
                else:
                    trans_instance = Transaction(row.source_bank_account_num, row.dest_bank_account_num, row.amount,
                                                 "credit")
                    trans_id, success = trans_instance.perform_transaction()

                    if not success:
                        print(f"move forward a credit transaction that failed:"
                              f"Source:  {row.source_bank_account_num}"
                              f"dest:  {row.dest_bank_account_num}"
                              f"Amount:  {row.amount}")

                        rows_this_id = Future_Transaction.select().where(Future_Transaction.trans_id == row.trans_id).\
                            order_by(Future_Transaction.time_for_transact.asc()).execute()

                        # if we have more trans at this ID - add to the end of the list
                        if rows_this_id:
                            new_time_for_trans = rows_this_id[-1] + 604800
                        else: # else if this is the last transaction with this ID - create new one from one week from now
                            new_time_for_trans = 604800

                        # Update the Future Transaction table
                        Future_Transaction.insert(
                            trans_id=row.trans_id,
                            source_bank_account_num=row.source_bank_account_num,
                            dest_bank_account_num=row.dest_bank_account_num,
                            amount=row.amount,
                            time_order=time.time(),
                            time_for_transact=new_time_for_trans).execute()

                    else: # if success the transaction - update bank account + update 'Transaction_Table' at DB
                        print(f"perform the following credit transaction:"
                              f"Source:  {row.source_bank_account_num}"
                              f"dest:  {row.dest_bank_account_num}"
                              f"Amount:  {row.amount}")
                        self._update_bank_account(trans_id=trans_id, src=row.source_bank_account_num,
                                                  dst=row.dest_bank_account_num,
                                                  amount=row.amount, direction="credit", success=success)

                    row.delete_instance()

    def _run_sql(self, query_func, *args, **kwargs):
        """
        This function is responsible for executing queries on the database.
        """
        self.c.execute(query_func(args, kwargs))

    def _add_log(self, msg, verbosity=Verbose.LOW):
        """
        adding msg to log with verbosity level:

        1. check if msg verbosity include verbosity file
        2. write file (self.server_log)

        Parameters:
        verbosity : verbosity level
            Enum - hold verbosity level of msg
        """
        if verbosity.value >= self.log_verbosity.value:
            with open(self.server_log, "a+") as log:
                now = datetime.now()
                log.write(
                    f'{now.strftime("%d/%m/%Y %H:%M:%S.%f")[:-3]} {msg}\n')

    def check_req_param_trans(self, req):
        """
        This function check that the user sent all the relevant details

        return:
        json of status
        """
        ret = {"Status": True, "Description": "Request_OK"}
        for attr in ["src_bank_account", "dst_bank_account", "amount", "direction"]:
            if attr not in req:
                print(f'fail req, missing {attr}')
                ret = {"Status": False, "Description": f'fail req, missing {attr}'}
                break

        if req["direction"].lower() != "debit" and req["direction"].lower() != "credit":
            ret = {"Status": False, "Description": f'fail req, Error direction!'}
        return ret

    @add_log
    def perform_trans(self, req):
        """
        This function preform transaction + Update this transaction info at the DB.

        Parameters:
        req: The json of the request from the user.
        """

        # check if the request if verify
        ret = self.check_req_param_trans(req)
        if not ret['Status']:
            return ret

        # create Transaction instance
        req["direction"] = req["direction"].lower()
        trans_instance = Transaction(req['src_bank_account'], req['dst_bank_account'], req['amount'], req["direction"])

        # if credit save the future transactions in the DB.
        if req["direction"] == 'credit':
            trans_id, success = trans_instance.perform_advance(req['dst_bank_account'], req['amount'])
            factor = 12

            current_time = time.time()
            add_week_sec = 604800  # 60*60*24*7
            for i in range(1, 12):
                Future_Transaction.insert(
                    trans_id=trans_id,
                    source_bank_account_num=req['src_bank_account'],
                    dest_bank_account_num=req['dst_bank_account'],
                    amount=float(req["amount"]) / 12,
                    time_order=time.time(),
                    time_for_transact=current_time + add_week_sec * i).execute()

        # if debit - make the transaction right now
        else:
            trans_id, success = trans_instance.perform_transaction()
            factor = 1

        if not success:
            # if credit fail - add to the end of all of the credits this transaction
            if req["direction"] == 'credit':
                add_week_sec = 604800  # 60*60*24*7
                Future_Transaction.insert(
                    trans_id=trans_id,
                    source_bank_account_num=req['src_bank_account'],
                    dest_bank_account_num=req['dst_bank_account'],
                    amount=float(req["amount"]) / 12,
                    time_order=time.time(),
                    time_for_transact=time.time() + add_week_sec * 12).execute()
            ret = {"Status": False, "Description": f'fail req, Error in Transaction - Need to look at Proccessor'}
            return ret

        # update bank account + update 'Transaction_Table' at DB
        self._update_bank_account(trans_id=trans_id,
                                  src=req['src_bank_account'],
                                  dst=req['dst_bank_account'],
                                  amount=float(req["amount"]) / factor,
                                  direction=req["direction"],
                                  success=success)

        return ret

    def _update_bank_account(self, trans_id, src, dst, amount, direction, success):
        """
        This function update the balance of the source and destination bank account's balance.

        Parameters:
        trans_id : current transaction id
        src: source bank account
        dst: destination bank account
        amount: amount of money at this transaction
        success: success status
        """
        query = bank_accounts.select().where(bank_accounts.number == src)
        current_query_bank_accounts_source = bank_accounts.get_by_id(query)

        current_query_bank_accounts_source.current_balance = bank_accounts.current_balance - amount
        current_query_bank_accounts_source.save()  # save new value

        query = bank_accounts.select().where(bank_accounts.number == dst)
        current_query_bank_accounts_dst = bank_accounts.get_by_id(query)

        current_query_bank_accounts_dst.current_balance = bank_accounts.current_balance + amount
        current_query_bank_accounts_dst.save()  # save new value

        # Update transaction at the DB.
        Transaction_Table.insert(
            transaction_id=trans_id,
            source_bank_account_num=src,
            dest_bank_account_num=dst,
            amount=amount,
            direction=direction,
            time_order=time.time(),
            status='success' if success else 'fail').execute()
