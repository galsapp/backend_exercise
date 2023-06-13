import processor


class Transaction():
    """
    This class is a transaction object
    """
    def __init__(self, src, dst, amount, direction, weeks_left=0):
        self.src = src
        self.dst = dst
        self.amount = amount
        self.direction = direction
        self.weeks_left = weeks_left
        self.amount_per_week = float(amount) / 12
        self.trans_id = -1

    def perform_transaction(self):
        """
        This function perform transaction at the processor 'black box'

        return:
        transaction id
        success status (bool)
        """
        try:
            self.trans_id, success = processor.perform_transaction(self.src, self.dst, self.amount, self.direction)
            return self.trans_id, success
        except Exception as e:
            print(f"error: {e}")
            return -1, False

    def perform_advance(self, dst_bank_account, amount):
        """
        This function perform transaction of a 'credit transaction' only at the processor 'black box'.

        return:
        transaction id
        success status (bool)
        """
        try:
            self.trans_id, success = processor.perform_transaction(self.src, self.dst, self.amount_per_week, 'credit')
            return self.trans_id, success
        except Exception as e:
            print(f"error: {e}")
            return -1, False
