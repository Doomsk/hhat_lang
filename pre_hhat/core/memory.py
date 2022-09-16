"""Memory"""
from pre_hhat.grammar.ast import AST
from pre_hhat.types.groups import (BaseGroup, Gate, GateArray)
from pre_hhat.types.builtin import (SingleInt, SingleStr, SingleBool, SingleNull,
                                    ArrayBool, ArrayInt, ArrayStr, ArrayCircuit)


class Memory:
    def __init__(self, name=None):
        if name is not None:
            self.stack = self._start()
            self.name = name
        else:
            self.name = None
            self.stack = dict()

    def init(self, name):
        if self.name is None:
            self.name = name
            self.stack = self._start()

    def _start(self):
        stack = {'name': self.name,
                 'var': dict(),
                 'return': SingleNull()}
        return stack

    @staticmethod
    def _init_var(type_expr):
        if isinstance(type_expr, tuple):
            if len(type_expr) == 2:
                _type = type_expr[0]
                _len = type_expr[1]
                _fixed_size = SingleBool('T')
                _data = type_expr[0](*[type_expr[0]().value_type(type_expr[0]().default[0]) for k in range(len(type_expr[1]))])
            else:
                _type = type_expr[0]
                _len = SingleInt(1)
                _fixed_size = SingleBool('F')
                _data = type_expr[0](type_expr[0]().value_type(type_expr[0]().default[0]))
        else:
            _type = type_expr
            _len = SingleInt(1)
            _fixed_size = SingleBool('F')
            _data = type_expr(type_expr.value_type(type_expr.default))
        return {'type': _type,
                'len': _len,
                'fixed_size': _fixed_size,
                'data': _data}

    def add_var(self, var_name, type_expr):
        if isinstance(var_name, (str, AST, SingleStr)) and var_name not in self.stack['var'].keys():
            self.stack['var'].update({var_name: self._init_var(type_expr.value)})

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            if key[0] in self.stack['var'].keys():
                if isinstance(key[1], (int, SingleInt)):
                    k1_keys = key[1] in self.stack['var'][key[0]]['data'].keys()
                    v_len = len(value) == self.stack['var'][key[0]]['len'].value[0]
                    if k1_keys and v_len:
                        self.stack['var'][key[0]]['data'][key[1]] = value
                    elif not self.stack['var'][key[0]]['fixed_size']:
                        self.stack['var'][key[0]]['data'][key[1]] = value
                        self.stack['var'][key[0]]['len'] = len(self.stack['var'][key[0]]['data'])
                if isinstance(key[1], tuple):
                    if len(key[1]) == len(value):
                        for idx, v in zip(key[1], value):
                            self.stack['var'][key[0]]['data'][idx] = v
                    else:
                        for idx in key[1]:
                            self.stack['var'][key[0]]['data'][idx] = value
                else:
                    self.stack['var'][key[0]][key[1]] = value
        if key in self.stack['var'].keys():
            for k in self.stack['var'][key]['data']:
                self.stack['var'][key]['data'] = value
        if key == 'return':
            self.stack['return'] = value

    def __getitem__(self, item):
        if isinstance(item, tuple):
            if item[0] in self.stack.keys():
                return self.stack[item[0]].get(item[1], SingleNull())
            if item[0] in self.stack['var'].keys():
                if item[1] in self.stack['var'][item[0]].keys():
                    return tuple(self.stack['var'][item[0]][item[1]])
            self.add_var(item[0], item[1])
            return tuple(self.stack['var'][item[0]])
        if item in self.stack.keys():
            return tuple(self.stack[item])
        if item in self.stack['var'].keys():
            return tuple(self.stack['var'][item]['data'].value)
        raise ValueError(f"No {item} found in memory.")

    def __contains__(self, item):
        if isinstance(item, tuple):
            if item[0] in self.stack['var'].keys():
                return item[1] in self.stack['var'][item[0]]['data'].indices
            return False
        return item[0] in self.stack.keys()


class SymbolTable:
    def __init__(self):
        self.table = {'main': None, 'func': dict()}

    def __getitem__(self, item):
        if item == 'main':
            return self.table['main']
        if item in self.table['func'].keys():
            return self.table['func'][item]
        raise ValueError(f"{self.__class__.__name__}: error when getting data from symbol table.")

    def __setitem__(self, key, value):
        if isinstance(value, (BaseGroup, AST, tuple)):
            if key == 'main':
                self.table['main'] = value
            else:
                self.table['func'].update({key: value})

    def __iadd__(self, other):
        if isinstance(other, (BaseGroup, AST)):
            self.table['main'] = other
        elif isinstance(other, tuple):
            self.table['func'].update({other[0]: other[1]})
        return self

    def __repr__(self):
        return f"{self.table}"
