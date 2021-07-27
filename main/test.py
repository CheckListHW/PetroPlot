import json

'''

ps_total = {'load.connections.aborts': 'Total', 'load.connections.running': 'Total',
            'load.connections.attempts_ps': 'Per Second', 'load.connections.succeeds_ps': 'Per Second',
            'load.scenarios.succeeds': 'Total', 'load.actions.attempts_ps': 'Per Second', 'load.actions.fails': 'Total'}

Load = {'load.connections.aborts': 'Load', 'load.connections.running': 'Load', 'load.connections.attempts_ps': 'Load', 'load.connections.succeeds_ps': 'Load', 'load.scenarios.succeeds': 'Load', 'load.actions.attempts_ps': 'Load', 'load.actions.fails': 'Load'}

merged = [
    {'name': key, 'kind': ps_total[key], 'category': Load[key]}
    for key in ps_total.keys()
]

res = json.dumps(merged,
                 sort_keys=True, indent=4, separators=(',', ': '))
print(res)

'''
ps_total = {'load.connections.aborts': 'Total', 'load.connections.running': 'Total',
            'load.connections.attempts_ps': 'Per Second', 'load.connections.succeeds_ps': 'Per Second',
            'load.scenarios.succeeds': 'Total', 'load.actions.attempts_ps': 'Per Second', 'load.actions.fails': 'Total'}

import os
if os.path.isfile('json.json'):
    os.remove('json.json')

jsonFile = open("json.json", mode="x")
json.dump(ps_total, jsonFile)
jsonFile.close()


