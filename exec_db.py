from peewee import Model, TextField, DateTimeField, SqliteDatabase, IntegerField, FloatField

db_file = 'my_db.db'
db = SqliteDatabase(db_file)

db_file_bank = 'bank.db'
db_bank = SqliteDatabase(db_file_bank)


class ExecDB(Model):
    class Meta:
        database = db

class ExecDB_bank(Model):
    class Meta:
        database = db_bank


class Transaction_Table(ExecDB):
    """

    """
    transaction_id = IntegerField()
    source_bank_account_num = IntegerField()
    dest_bank_account_num = IntegerField()
    amount = FloatField()
    direction = TextField()
    time_order = DateTimeField()
    status = TextField()

    class Meta:
        db_table = 'Transaction_Table'


class Future_Transaction(ExecDB):
    """

    """
    trans_id = IntegerField()
    source_bank_account_num = IntegerField()
    dest_bank_account_num = IntegerField()
    amount = FloatField()
    time_order = DateTimeField()
    time_for_transact = DateTimeField()

    class Meta:
        db_table = 'Future_Transaction'


class bank_accounts(ExecDB_bank):
    """

    """
    number = IntegerField()
    current_balance = FloatField()

    class Meta:
        db_table = 'bank_accounts'


tables = [Transaction_Table, Future_Transaction, bank_accounts]
queries = ["select", "insert", "delete", "update", "get"]
