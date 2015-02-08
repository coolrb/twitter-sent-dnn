"""
Sampling hyper parameters
"""

import numpy as np
import random
from collections import OrderedDict
import sys

# domain range and configs
CONSTS = OrderedDict()

# Semantic:
# - repeat: iid sampling repeat
# - values: choices to samplen from
# - default: the default value to use if `on` is false
# - on: whether to sample it or nor
# - depends_on: the array length depends on the given variable name

CONSTS['conv_layer_n'] = {
    'values': [2, 3],
    'default': 2,
    'on': False
}
CONSTS['fold'] = {
    'values': [0, 1], 
    'depends_on': 'conv_layer_n', 
    'default': 1,
    'repeat': True,
    'on': False
}
CONSTS['dr'] = {
    'values': [0.5], 
    'depends_on': 'conv_layer_n',
    'on': True
}
CONSTS['ext_ebd'] = {
    'values': [True, False],
    'default': False,
    'on': False
}
CONSTS['batch_size'] = {
    'values': [9, 10, 11, 12], 
    'default': 10,
    'on': False
}
CONSTS['ebd_dm'] = {
    'values': [48],
    'on': True
}

CONSTS['l2_regs'] = {
    'values': [1e-4, 1e-5, 1e-6],
    'depends_on': 'conv_layer_n+2',
    'on': True
}

def coin_toss(p = 0.5):
    return np.random.binomial(n = 1, p = p, size = (1, ))

# semi-random ones
SEMI_RANDOM_PARAMS = {
    'ks': {
        2: (20, 5), 
        3: (20, 10, 5)
    }, 
    'nkerns': {
        2: (6, 12), 
        3: (5, 10, 18)
    }, 
    'filter_widths': {
        2: (10, 7), 
        3: (6, 5, 3)
    }, 
    'l2_regs': {
        2: (1e-6, 3e-5, 3e-5, 1e-4),
        3: (1e-6, 3e-5, 3e-6, 1e-5, 1e-4),
    }
}

def get_possibility_n():
    """
    Get the possibility count of the current configuration
    """
    possibility_n = 1
    params = {}
    for key in CONSTS:
        if not CONSTS[key]['on']:
            assert CONSTS[key].has_key('default'), "if ON is False, then a default must be provided"
            if CONSTS[key].has_key('default'):
                CONSTS[key]['values'] = [CONSTS[key].get('default')]
        
        depends_on = CONSTS[key].get('depends_on')
        candidates = CONSTS[key]['values']
        
        if depends_on:                
            if '+' in depends_on: # extra times
                name, extra_n_str = depends_on.split('+')
                dup_times = params[name] + int(extra_n_str.strip())
            else:
                dup_times = params[depends_on]

            if CONSTS[key].get('repeat'):
                possibility_n *= len(candidates)
                params[key] = tuple([random.choice(CONSTS[key]['values'])]) * dup_times
            else:
                possibility_n *= (len(candidates) ** dup_times)
                params[key] = tuple([random.choice(CONSTS[key]['values']) for _ in xrange(dup_times)])
        else:
            params[key] = random.choice(CONSTS[key]['values'])
            possibility_n *= len(candidates)

    return possibility_n

def sample_params(n = None, semi_random_params_key = 'conv_layer_n'):
    if n is None:
        n = get_possibility_n()
    else:
        possibility_n = get_possibility_n()
        assert n <= possibility_n, "%d > %d" %(n, possibility_n)
        
    pool = set()
    samples = []
    i = 0

    sys.stderr.write('total: %d\n' %(get_possibility_n()))

    while i < n:
        # random hyper parameters        
        params = {}
        for key in CONSTS:
            if not CONSTS[key]['on']:
                if CONSTS[key].get('default'):
                    CONSTS[key]['values'] = [CONSTS[key].get('default')]
            
            depends_on = CONSTS[key].get('depends_on')
            value = random.choice(CONSTS[key]['values'])
            if depends_on:
                
                if '+' in depends_on: # extra times
                    name, extra_n_str = depends_on.split('+')
                    dup_times = params[name] + int(extra_n_str.strip())
                else:
                    dup_times = params[depends_on]

                if CONSTS[key].get('repeat'):
                    params[key] = tuple([value]) * dup_times
                else:
                    params[key] = tuple([random.choice(CONSTS[key]['values']) for _ in xrange(dup_times)])
            else:
                if isinstance(value, bool): #it's bool, show or hide
                    if value:
                        params[key] = value
                else:
                    params[key] = value
        
        for key in SEMI_RANDOM_PARAMS:
            if not (CONSTS.get(key) and CONSTS[key]['on']):
                params[key] = SEMI_RANDOM_PARAMS[key][params[semi_random_params_key]]
            
        if tuple(params.values()) in pool:
            continue
        else:
            i += 1
            sys.stderr.write("i = %d: %r\n" %(i, params))
            pool.add(tuple(params.values()))
            samples.append(params)
            
    return samples

def _format_value(v, tuple_sep = ' '):
    if isinstance(v, tuple):
        return tuple_sep.join(map(str, v))
    elif isinstance(v, bool):
        return ''
    else:
        return str(v)

def format_params_to_cmd(name, params, prefix = "python cnn4nlp.py --corpus_path=data/twitter.pkl --model_path=models/twitter.pkl --l2  --norm_w --ebd_delay_epoch=0 --au=tanh --n_epochs=10"):
    params_str = params2str(params)
    sig = params2str(params, cmd_sep = ',,', key_val_sep = '=', tuple_sep = ',', key_prefix = '')
    return "%s %s --img_prefix=%s,,%s"%(
        prefix, params_str, name, sig
    )

def params2str(params, cmd_sep = ' ',key_val_sep = ' ', tuple_sep = ' ', key_prefix = '--'):
    return cmd_sep.join(["%s%s%s%s"  %(key_prefix, 
                                       key, 
                                       key_val_sep, 
                                       _format_value(value, tuple_sep = tuple_sep))
                         for key, value in params.items()])
    
if __name__ ==  "__main__":
    import sys
    name = sys.argv[1]
    if len(sys.argv) > 2:
        possibility_n = int(sys.argv[2])
    else:
        possibility_n = None

    # print "possibility_n = %d" %(possibility_n)
    for param in sample_params(possibility_n):
        print format_params_to_cmd(name, param)
