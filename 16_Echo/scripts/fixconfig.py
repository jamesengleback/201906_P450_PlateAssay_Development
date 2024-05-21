import json

with open('wells.json', 'r') as f:
    wells= json.load(f)
with open('../.config_16.json', 'r') as f: 
    _cfg = json.load(f)
    cfg = deepcopy(_cfg)
for block_key, block in zip(_cfg['blocks'].keys(), _cfg['blocks'].values()):
    k = block['k']
    concs = np.linspace(0,1,8)**k * 500
    cfg['blocks'][block_key]['concentrations'] = list(concs)
    cfg['blocks'][block_key]['test_wells'] = wells[block_key]['test_wells']
    cfg['blocks'][block_key]['control_wells'] = wells[block_key]['control_wells']
with open('../config_16.json', 'w') as f:
    json.dump(cfg, f)
