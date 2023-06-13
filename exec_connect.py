from flask import Flask, request

from exec_server import ExecManager

app = Flask(__name__)
ex = ExecManager()


@app.route('/perform_transaction', methods=['POST'])
def perform_transaction():
    ret = ex.perform_trans(request.json)
    return ret
