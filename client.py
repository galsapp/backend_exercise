# This is a client helper file for sending post requests

import requests

# new trans
trans = {'src_bank_account': '1234', 'dst_bank_account': '5678', 'amount': '12000', 'direction': 'credit'}

# call restAPI post request
print("post request:")
resp = requests.post('http://localhost:5000/perform_transaction', json=trans)

# Print response - post request
print(resp.content.decode("utf-8"))
