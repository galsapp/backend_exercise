import json
from pathlib import Path

from waitress import serve

import exec_connect

f = open(str(Path(__file__).parent.absolute()) + '/settings/testConfig.json')
test_config_data = json.load(f)

# welcome to server
print("The server is on!")
print("Waiting for a new request")

# open server
serve(exec_connect.app, host='0.0.0.0', port=test_config_data["PORT"])
