"""Symbolic for Pre Evaluation"""

from copy import deepcopy

"""
AST = tuple of objects (new_ast) 

FuncScopeTable - splits into 'main' and other functions funcs. i.e.: {'main': {}, 'funcs': {}}
VarScopeTable
BranchScopeTable



example:

func int Sum (int x, int y) ( return (add(x y)) )

main null X: ( 
 int a = (:3, :print('aoa'), :add(5), :print)
 int(3) b = (:10, 0:add(5), (1 2):add(-5), :print, (0 1):print('oi'))
 print(Sum(a b))
)

Program(
        Function(Token(function), (FuncTemplate(Symbol(Sum), Type(int), Params(...), Body(...)))),
        Function(Token(main), (FuncTemplate(Symbol(X), Type(null), Body(...)))),
        ...
        )

PreEvaluator -> 
(
    FST = {'main': {'X': (main's AST)},
           'funcs': {'Sum': (func's AST)}}
    VST = {'main': {'X': {'a': {'len': 1, 'type': 'int', 'data': {0: current_value}}},
                     {'b': {'len': 3, 'type': 'int', 'data': {0: cur, 1: cur, 2: cur}
                }},
            'funcs': {}}
    BST = {0: (AST body1 + exit_cond_body), ...}
)

Evaluator -> 
(
    AST = (FST(main(X)),)
)
"""


class FST:
    table = {'main': dict(), 'func': dict(), 'cur': dict(), 'scope': dict()}

    @staticmethod
    def set_default():
        return {'type': None, 'params': (), 'body': (), 'return': ()}

    @classmethod
    def create(cls, name=None, func=None):
        if name is None and func is None:
            if not cls.table['cur']:
                cls.table['cur'] = cls.set_default()
        else:
            if name not in cls.table['scope'].keys() and func in ['main', 'func']:
                cls.table['scope'].update({name: func})
                cls.table[func].update({name: cls.set_default()})

    @classmethod
    def add(cls, value, name=None, key=None):
        if name is None:
            if key is not None:
                cls.table['cur'][key] = value
            else:
                raise ValueError("Key must be 'type', 'params', 'body' or 'return'.")
        else:
            _func = cls.table['scope'].get(name, False)
            if _func:
                cls.table[_func][name][key] = value

    @classmethod
    def is_func(cls, name):
        return name in cls.table['scope'].keys()

    @classmethod
    def move_cur_to(cls, name):
        _func = cls.table['scope'].get(name, False)
        if _func:
            _new_data = deepcopy(cls.table['cur'])
            cls.table[_func][name] = _new_data
            cls.free_cur()

    @classmethod
    def free_cur(cls):
        cls.table['cur'] = cls.set_default()

    @classmethod
    def __repr__(cls):
        return f"{cls.table}"


class Memory:
    data = {}

    def __init__(self):
        pass

    @classmethod
    def set_default(cls):
        return {'cur': {}, 'func': {}, 'main': {}}

    @classmethod
    def set_var_mem(cls, type_data=None):
        if type_data in ['bool', 'int', 'float', 'str']:
            return {'type': type_data, 'len': 1, 'data': {}}
        if type_data in ['circuit']:
            return {'type': type_data, 'len': 1, 'data': []}
        if type_data in ['hashmap', 'measurement']:
            return {'type': type_data, 'len': 1, 'data': {}}
        if type in [None, 'null']:
            return {'type': None, 'len': 0, 'data': {}}

    @classmethod
    def set_var_data(cls, type_data, len_data=None):
        if type_data == 'null':
            return {}
        if type_data == 'bool':
            if not len_data:
                return {0: None}
            return {k: None for k in range(len_data)}
        if type_data == 'int':
            if not len_data:
                return {0: 0}
            return {k: 0 for k in range(len_data)}
        if type_data == 'float':
            if not len_data:
                return {0: 0.0}
            return {k: 0.0 for k in range(len_data)}
        if type_data == 'str':
            if not len_data:
                return {0: ''}
            return {k: '' for k in range(len_data)}
        if type_data == 'circuit':
            return []
        if type_data in ['hashmap', 'measurement']:
            return {}
        return {}

    @classmethod
    def start(cls):
        if not cls.data:
            cls.data = cls.set_default()
        else:
            raise ValueError("Memory already started.")

    @classmethod
    def restart(cls):
        cls.data = cls.set_default()

    @classmethod
    def create(cls, scope, name, var=None, type_data=None):
        if scope in cls.data.keys():
            if name in cls.data[scope].keys():
                if var not in cls.data[scope][name].keys() and var is not None:
                    cls.data[scope][name].update({var: cls.set_var_mem(type_data)})
                    cls.data[scope][name][var]['data'] = cls.set_var_data(type_data)
            else:
                if var:
                    cls.data[scope].update({name: {var: cls.set_var_mem(type_data)}})
                else:
                    cls.data[scope].update({name: {}})

                if type_data:
                    cls.data[scope][name][var]['data'] = cls.set_var_data(type_data)

    @classmethod
    def write(cls, scope, name, var, value, index=None, prop=None):
        if scope in cls.data.keys():
            if name in cls.data[scope].keys():
                if var in cls.data[scope][name].keys():
                    if prop is None and index is not None:
                        if cls.data[scope][name][var]['type'] not in ['circuit']:
                            if index in cls.data[scope][name][var]['data'].keys():
                                if cls.data[scope][name][var]['type'] in ['int', 'float', 'str']:
                                    cls.data[scope][name][var]['data'][index] = value
                                elif cls.data[scope][name][var]['type'] in ['hashmap',
                                                                            'measurement']:
                                    cls.data[scope][name][var]['data'].update({index: value})
                            else:
                                if cls.data[scope][name][var]['type'] in ['hashmap', 'measurement']:
                                    cls.data[scope][name][var]['data'].update({index: value})
                        else:
                            if isinstance(value, list):
                                cls.data[scope][name][var]['data'].extend(value)
                            else:
                                cls.data[scope][name][var]['data'].append(value)
                    elif prop is not None:
                        if prop in cls.data[scope][name][var].keys():
                            cls.data[scope][name][var][prop] = value
                            if prop == 'len':
                                type_data = cls.data[scope][name][var]['type']
                                cls.data[scope][name][var]['data'] = cls.set_var_data(
                                    type_data=type_data,
                                    len_data=value)
                    else:
                        if cls.data[scope][name][var]['type'] in ['circuit']:
                            if isinstance(value, list):
                                cls.data[scope][name][var]['data'].extend(value)
                            else:
                                cls.data[scope][name][var]['data'].append(value)

    @classmethod
    def append(cls, scope, name, var, index, value):
        if scope in cls.data.keys():
            if name in cls.data[scope].keys():
                if index in cls.data[scope][name][var]['data'].keys():
                    cls.data[scope][name][var]['data'][index] += value

    @classmethod
    def read(cls, scope, name, var, index=None, prop=None):
        if scope in cls.data.keys():
            if name in cls.data[scope].keys():
                if var in cls.data[scope][name].keys():
                    if index is None and prop is None:
                        if cls.data[scope][name][var]['type'] not in ['circuit', 'hashmap',
                                                                      'measurement']:
                            return tuple(k for k in cls.data[scope][name][var]['data'].values())
                        return tuple(cls.data[scope][name][var]['data'])
                    if prop in cls.data[scope][name][var].keys():
                        return cls.data[scope][name][var][prop]
                    if cls.data[scope][name][var]['type'] not in ['circuit']:
                        if index in cls.data[scope][name][var]['data'].keys():
                            if cls.data[scope][name][var]['type'] in ['hashmap', 'measurement']:
                                return {index: cls.data[scope][name][var]['data'][index]}
                            return cls.data[scope][name][var]['data'][index]
                    return tuple(cls.data[scope][name][var]['data'])
        raise ValueError(f"Error reading var '{var}'.")

    @classmethod
    def copy(cls, from_var, to_var):
        valid_keys = {'scope', 'name', 'var', 'data', 'len', 'type'}
        from_valid_set = set(from_var.keys()).symmetric_difference(valid_keys)
        to_valid_set = set(to_var.keys()).symmetric_difference(valid_keys)
        if not from_valid_set and not to_valid_set:
            if from_var['type'] == to_var['type']:
                from_data = cls.data[from_var['scope']][from_var['name']][from_var['var']]
                to_data = cls.data[to_var['scope']][to_var['name']][to_var['var']]
                to_data['data'] = deepcopy(from_data['data'])
                to_data['len'] = from_data['len']
            else:
                raise ValueError("From var e to var are no the same type.")
        else:
            raise ValueError(f"No valid from and to var to copy.")

    @classmethod
    def get_idx(cls, scope, name, var):
        if cls.data[scope][name][var]['type'] not in ['circuit']:
            return tuple(k for k in cls.data[scope][name][var]['data'].keys())
        else:
            return tuple(k for k in range(cls.data[scope][name][var]['len']))

    @classmethod
    def return_prop_or_idx(cls, scope, name, var, data):
        if scope in cls.data.keys():
            if name in cls.data[scope].keys():
                if var in cls.data[scope][name].keys():
                    if data in cls.data[scope][name][var].keys():
                        return cls.data[scope][name][var][data]
                    if data in cls.data[scope][name][var]['data'].keys():
                        return cls.data[scope][name][var]['data'][data]
        raise ValueError(f"Something got wrong here: {scope}->{name}->{var}->{data}.")

    @classmethod
    def is_func(cls, name):
        return name in cls.data['func'].keys() or name in cls.data['main'].keys()

    @classmethod
    def is_var(cls, scope, name, var):
        if scope in cls.data.keys():
            if name in cls.data[scope].keys():
                return var in cls.data[scope][name].keys()
        return False

    @classmethod
    def move(cls, from_scope, to_scope):
        _from_scope = deepcopy(cls.data[from_scope])
        cls.data[to_scope] = _from_scope
        cls.free(scope=from_scope)

    @classmethod
    def free(cls, scope=None, name=None):
        if scope is None:
            if name is None:
                cls.data = cls.set_default()
        else:
            if name is None:
                cls.data[scope] = dict()
            else:
                cls.data[scope][name] = dict()

    def __repr__(self):
        return f"{self.data}"
