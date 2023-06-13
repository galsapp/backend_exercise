import random
import sys

'''
This File simulate the processor 'black box'
'''


def perform_transaction(src, dst, amount, direction):
    """All black box"""
    return random.randint(0, sys.maxsize), True


def download_report():
    """All black box"""
    print("GET DAILY REPORT OF LAST 5 DAYS")
