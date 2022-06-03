"""Evaluator"""

import time
import ast
from copy import deepcopy
from typing import Any
import networkx as nx
from qiskit import QuantumCircuit
from qiskit.providers.aer import QasmSimulator
from rply.token import BaseBox, Token
from hhat_lang.tokens import tokens
from hhat_lang.lexer import lexer
from hhat_lang.parser import parser
from hhat_lang.symbolic import FST, Memory
from hhat_lang.data_types import (int_type, float_type, str_type,
                                  bool_type, circuit_type, literal_type)
from hhat_lang.new_ast import (Program, Function, FuncTemplate, ParamsSeq, AThing, Body,
                               AttrDecl, Expr, ManyExprs, Entity, AttrAssign, Call,
                               Func, IfStmt, ElifStmt, ElseStmt, Tests, ForLoop, ExitBody,
                               AttrHeader, TypeExpr, IndexAssign, Args, Caller)
from hhat_lang.builtin import (btin_print, btin_and, btin_or, btin_not, btin_eq, btin_neq,
                               btin_gt, btin_gte, btin_lt, btin_lte, btin_add, btin_mult,
                               btin_div, btin_pow, btin_sqrt, btin_q_h, btin_q_x, btin_q_z,
                               btin_q_sync, btin_q_cnot, btin_q_toffoli, btin_q_init,
                               btin_q_and, btin_q_or)

SAMPLE_CODE_1 = """
func null f: ( int b =(:4) ) 

func int sum (int x, int y) (
    return (add(x y))
)

main null X: (
    int a =(:3)
    int b =(:5)
    if (eq(a b)): (
        print('eq')
    ) 
    elif (gt(a b)): (
        print('gt')
    ) 
    else: (
        print('lt')
    )
    circuit @c1 = (:@h)
)
"""

SAMPLE_CODE_2 = """
main null V: (
    circuit(2) @c1 = (1:@x)
    int a = (:5, :add(3 @c1), :print('test'))
    int(4) b = (0:1, 2:10, :add(100), :print, (1 3):print)
    circuit(3) @c2 = (0:@h, (0 1):@cnot)
    hashmap x = (0:1, 1:'oi', :print)
    measurement y = (:@c2, :print)
    circuit(4) @c3 = (:@h)
    circuit(8) @c4 = ((0 1 2 3):@c3)
    measurement z = (:@c4, :print('res:'))
    measurement z2 = (:@c4(1 2 7 8), :print('new res:'))
)
"""


# noinspection PyArgumentList
class Eval:
    def __init__(self, debug=False):
        self.debug = debug
        self.mem = Memory()
        self.mem.restart()
        self.func_dict_order = ['type', 'params', 'body', 'return']
        self.tasks = {dict: self.exec_dict,
                      tuple: self.exec_tuple,
                      str: self.exec_str,
                      ParamsSeq: self.ast_paramsseq,
                      AThing: self.ast_athing,
                      Body: self.ast_body,
                      AttrDecl: self.ast_attrdecl,
                      AttrAssign: self.ast_attrassign,
                      Expr: self.ast_expr,
                      ManyExprs: self.ast_manyexprs,
                      Entity: self.ast_entity,
                      Call: self.ast_call,
                      Func: self.ast_func,
                      IfStmt: self.ast_ifstmt,
                      ElifStmt: self.ast_elifstmt,
                      ElseStmt: self.ast_elsestmt,
                      Tests: self.ast_tests,
                      ExitBody: self.ast_exitbody,
                      ForLoop: self.ast_forloop,
                      AttrHeader: self.ast_attrheader,
                      TypeExpr: self.ast_typeexpr,
                      IndexAssign: self.ast_indexassign,
                      Args: self.ast_args,
                      Caller: self.ast_caller,
                      Token: self.ast_token
                      }
        self.type_lookup = {
            # TODO: check if literal_type is valid then refactor calls below
            'INT_LITERAL': int_type,
            'STR_LITERAL': str_type,
            'FLOAT_LITERAL': float_type,
            'TRUE_LITERAL': bool_type,
            'FALSE_LITERAL': bool_type,
        }
        self.btin_funcs = {'print': btin_print,
                           'add': btin_add,
                           'eq': btin_eq,
                           '@x': btin_q_x,
                           '@h': btin_q_h,
                           '@cnot': btin_q_cnot,
                           '@init': btin_q_init,
                           '@and': btin_q_and,
                           '@or': btin_q_or}
        self.trans_gates = {'X': 'x',
                            'H': 'h',
                            'CNOT': 'cx',
                            'SWAP': 'swap'}
        self.op_rules = {'add': self.morpher,
                         '@h': self.appender,
                         '@x': self.appender,
                         '@cnot': self.appender,
                         'print': self.nuller}

    # DEBUG PRINT

    def dp(self, scope, *msg, **msgs):
        if self.debug:
            print(f'* [{scope}]:', *msg, **msgs)

    # MAIN EXECUTER FUNCTIONS

    def exec_dict(self, code, stats):
        if stats['scope'] is None:
            # old_stats = deepcopy(stats)
            if 'main' in code.keys():
                stats['scope'] = 'main'
                stats = self.tasks[type(code['main'])](code['main'], stats)
            elif 'func' in code.keys():
                stats['scope'] = 'func'
                stats = self.tasks[type(code['func'])](code['func'], stats)
            else:
                if len(code.keys()) == 1:
                    print('??')

            # stats = old_stats
        elif stats['scope'] == 'main':
            if not stats['func']:
                stats['func'] = list(code.keys())[0]
                stats = self.tasks[type(code[stats['func']])](code[stats['func']], stats)
            else:
                if not set(self.func_dict_order).symmetric_difference(code.keys()):
                    self.dp('dict', 'executing inside function (main)')
                    for k in self.func_dict_order:
                        if k in code.keys():
                            self.dp('dict', f'code: key={k} | code={code[k]}')
                            stats['key'] = k
                            stats = self.tasks[type(code[k])](code[k], stats)

        elif stats['scope'] == 'func':
            if not stats['func']:
                stats['func'] = list(code.keys())[0]
                stats = self.tasks[type(code[stats['func']])](code[stats['func']], stats)
            if not set(self.func_dict_order).symmetric_difference(code.keys()):
                self.dp('dict', 'executing inside function (func)')
                for k in self.func_dict_order:
                    if k in code.keys():
                        stats['key'] = k
                        stats = self.tasks[type(code[k])](code[k], stats)

        return stats

    def exec_tuple(self, code, stats):
        # old_stats = deepcopy(stats)
        for k in code:
            self.dp('tuple', f'code: key/code={k}')
            if stats['skip'] == 0:
                stats = self.tasks[type(k)](k, stats)
                self.dp('tuple', f'skip or not? {stats["skip"]}')
                if stats['skip'] > 0:
                    stats['skip'] -= 1
                    # stats['level'] = += 1 , stats['skip']
                    break
        # stats = old_stats
        return stats

    def exec_str(self, code, stats):
        if stats['key'] == 'type':
            res = self.resolve_literal(code)
            self.mem.write(scope=stats['scope'], name=stats['func'], var=stats['var'], prop='type',
                           value=res)

        elif stats['key'] == 'params':
            pass

        elif stats['key'] == 'body':
            self.dp('str', 'body')
            if code == 'all' and stats['func'] and stats['var'] and stats['type']:
                stats['idx'] = self.mem.get_idx(scope=stats['scope'], name=stats['func'],
                                                var=stats['var'])
                self.dp('str', f'got all {stats["idx"]}')

        elif stats['key'] == 'return':
            pass

        self.dp('str', f'- str={code} | key={stats["key"]}')
        return stats

    # AST OBJECTS FUNCTIONS

    def ast_paramsseq(self, code, stats):
        stats = self.tasks[type(code.value)](code.value, stats)
        return stats

    def ast_athing(self, code, stats):
        stats = self.tasks[type(code.value)](code.value, stats)
        return stats

    def ast_body(self, code, stats):
        stats['obj'] = Body
        stats = self.tasks[type(code.value)](code.value, stats)
        if stats['obj'] == AttrDecl:
            stats['obj'] = None
        return stats

    def ast_attrdecl(self, code, stats):
        self.dp('attrdecl', 'entered')
        stats['obj'] = AttrDecl
        stats = self.tasks[type(code.value)](code.value, stats)
        if stats['to_var']:
            res = stats['to_var']
            if len(res) == len(stats['idx']):
                for k, r in zip(stats['idx'], res):
                    sub_r = self.resolve_literal(r)
                    self.mem.write(scope=stats['scope'], name=stats['func'], var=stats['var'],
                                   index=k, value=sub_r)
            elif len(res) == 1:
                for k in stats['idx']:
                    self.mem.write(scope=stats['scope'], name=stats['func'], var=stats['var'],
                                   index=k, value=res[0])
        stats['var'] = None
        stats['type'] = None
        stats['obj'] = None
        self.dp('attrdel', 'left')
        return stats

    def ast_attrassign(self, code, stats):
        stats['obj'] = AttrAssign
        stats = self.tasks[type(code.value)](code.value, stats)
        if stats['to_var']:
            res = stats['to_var']
            if len(res) == len(stats['idx']):
                for k, r in zip(stats['idx'], res):
                    sub_r = self.resolve_literal(r)
                    self.mem.write(scope=stats['scope'], name=stats['func'], var=stats['var'],
                                   index=k, value=sub_r)
            elif len(res) == 1:
                if stats['type'] not in ['circuit']:
                    for k in stats['idx']:
                        self.mem.write(scope=stats['scope'], name=stats['func'], var=stats['var'],
                                       index=k, value=res[0])
                else:
                    self.mem.write(scope=stats['scope'], name=stats['func'], var=stats['var'],
                                   value=res[0])
        stats['obj'] = None
        return stats

    def ast_expr(self, code, stats):
        # stats['obj'] = Expr
        stats = self.tasks[type(code.value)](code.value, stats)
        return stats

    def ast_manyexprs(self, code, stats):
        stats = self.tasks[type(code.value)](code.value, stats)
        return stats

    def ast_entity(self, code, stats):
        stats = self.tasks[type(code.value)](code.value, stats)
        res = self.resolve_args(stats['to_var'], stats)
        self.dp('entity', f'res={res}')
        if len(res) == len(stats['idx']) and stats['type'] != 'circuit':
            if stats['type'] != 'circuit':
                for k, v in zip(stats['idx'], res):
                    sub_v = self.resolve_literal(v)
                    self.mem.write(scope=stats['scope'], name=stats['func'], var=stats['var'],
                                   index=k,
                                   value=sub_v)
            else:
                self.mem.write(scope=stats['scope'], name=stats['func'], var=stats['var'],
                               value=res[0])
        elif len(res) == 1:
            if stats['type'] != 'circuit':
                for k in stats['idx']:
                    self.mem.write(scope=stats['scope'], name=stats['func'], var=stats['var'],
                                   index=k,
                                   value=res[0])
            else:
                self.mem.write(scope=stats['scope'], name=stats['func'], var=stats['var'],
                               value=res[0])
        else:
            if stats['type'] == 'circuit':
                for k in res:
                    self.mem.write(scope=stats['scope'],
                                   name=stats['func'],
                                   var=stats['var'],
                                   value=k)
        stats['to_var'] = ()
        stats['args'] = ()
        stats['idx'] = ()
        stats['from_var'] = ()
        return stats

    def ast_call(self, code, stats):
        self.dp('call', 'entered')
        prev_obj = stats['obj']
        stats['obj'] = Call
        stats = self.tasks[type(code.value)](code.value, stats)
        if prev_obj == Tests:
            pass
        stats['obj'] = None
        self.dp('call', 'left')
        return stats

    def ast_func(self, code, stats):
        stats = self.tasks[type(code.value)](code.value, stats)
        return stats

    def ast_ifstmt(self, code, stats):
        self.dp('if-stmt', 'entered')
        stats = self.tasks[type(code.value)](code.value, stats)
        self.dp('if-stmt', 'left')
        return stats

    def ast_elifstmt(self, code, stats):
        self.dp('elif-stmt', 'entered')
        stats = self.tasks[type(code.value)](code.value, stats)
        self.dp('elif-stmt', 'left')
        return stats

    def ast_elsestmt(self, code, stats):
        self.dp('else-stmt', 'entered')
        stats = self.tasks[type(code.value)](code.value, stats)
        self.dp('else-stmt', 'left')
        return stats

    def ast_tests(self, code, stats):
        stats['obj'] = Tests
        stats = self.tasks[type(code.value)](code.value, stats)
        if stats['level'] != 0:
            stats['level'] += 1

        return stats

    def ast_exitbody(self, code, stats):
        stats['skip'] += 2
        return stats

    def ast_forloop(self, code, stats):
        stats['obj'] = ForLoop
        stats = self.tasks[type(code.value)](code.value, stats)
        return stats

    def ast_attrheader(self, code, stats):
        stats['obj'] = AttrHeader
        stats = self.tasks[type(code.value)](code.value, stats)
        _scope = stats['scope']
        _func = stats['func']
        _type = stats['type']
        _var = stats['var']
        self.dp('attrheader', f'res: {stats}')
        self.dp('attrheader', f'- scope={_scope} func={_func} var={_var} type={_type}')
        if _scope and _func and _type and _var:
            self.dp('attrheader', '... ok!')
            self.mem.create(scope=_scope, name=_func, var=_var, type_data=_type)
            if stats['args']:
                self.mem.write(scope=_scope, name=_func, var=_var, prop='len',
                               value=stats['args'][0])
                stats['args'] = ()
            self.dp('memory', f'** MEMORY={self.mem} **')
            stats['obj'] = AttrAssign
        return stats

    def ast_typeexpr(self, code, stats):
        old_obj = stats['obj']
        stats['obj'] = TypeExpr
        stats = self.tasks[type(code.value)](code.value, stats)
        stats['obj'] = old_obj
        return stats

    def ast_indexassign(self, code, stats):
        prev_obj = stats['obj']
        stats['obj'] = IndexAssign
        stats = self.tasks[type(code.value)](code.value, stats)
        stats['obj'] = prev_obj
        return stats

    def ast_args(self, code, stats):
        stats['obj'] = Args
        stats = self.tasks[type(code.value)](code.value, stats)
        return stats

    def ast_caller(self, code, stats):
        stats['obj'] = Caller
        stats = self.tasks[type(code.value)](code.value, stats)
        return stats

    def ast_token(self, code, stats):
        self.dp('token', f'token got={code} | obj={stats["obj"]}')

        if stats['obj'] == AttrHeader:
            if not stats['var']:
                if code.name.endswith('SYMBOL'):
                    stats['var'] = code.value
            elif not stats['type']:
                if code.name.endswith('TYPE') or code.name.endswith('SYMBOL'):
                    stats['type'] = code.value

        elif stats['obj'] == IndexAssign:
            res = self.resolve_literal(code)
            stats['idx'] += (res,)

        elif stats['obj'] == Args:
            if code.name.endswith('LITERAL'):
                res = self.resolve_literal(code)
                stats['args'] += (res,)
            elif code.name == 'SYMBOL':
                self.dp('symbol as args?')
            elif code.name == 'QSYMBOL':
                self.dp('qsymbol as args?')

        elif stats['obj'] == Call:
            self.dp('token', f'obj=call code={code.value}')
            if stats['var'] and stats['type']:
                res = ()
                if code.name.endswith('BUILTIN') or code.name.endswith('GATE'):
                    for k in stats['args']:
                        res += (k,)
                    for k in stats['idx']:
                        res += (self.mem.read(scope=stats['scope'],
                                              name=stats['func'],
                                              var=stats['var'],
                                              index=k),)
                    self.dp('token', f'obj=call res={res}')
                    args = self.resolve_args(res, stats)
                    res = self.btin_funcs[code.value](*args)
                    if stats['var'] and stats['type'] and res:
                        stats['to_var'] += (res,)
                elif code.name == 'SYMBOL':
                    args = stats['args']
                    new_args = ()
                    for k in args:
                        if isinstance(k, int):
                            new_args += (k,)
                        elif isinstance(k, Token):
                            if k.name.endswith('LITERAL'):
                                new_args += (ast.literal_eval(k.value),)
                            elif k.name == 'SYMBOL':
                                new_args += (self.mem.read(scope=stats['scope'],
                                                           name=stats['func'],
                                                           var=k.value),)
                            elif k.name == 'QSYMBOL':
                                self.dp('token', f'obj=call | codetype=qsymbol')
                            else:
                                self.dp('token', f'!!UNKNOWN ARG FOUND!! {k}')
                    for k in new_args:
                        res += (self.mem.read(scope=stats['scope'],
                                              name=stats['func'],
                                              var=code.value,
                                              index=k),)
                    stats['to_var'] += (res,)
                elif code.name == 'QSYMBOL':
                    args = stats['args']
                    args_type = set([type(k) for k in args])
                    if len(args_type) == 1:
                        if {int}.issubset(args_type) or {str}.issubset(args_type):
                            # func to write qasm
                            circuit_data = self.mem.read(scope=stats['scope'],
                                                         name=stats['func'],
                                                         var=code.value,
                                                         prop='data')
                            circuit_len = self.mem.read(scope=stats['scope'],
                                                        name=stats['func'],
                                                        var=code.value,
                                                        prop='len')
                            circuit_qasm = self.circuit_to_qasm(circuit_data, circuit_len)
                            simu = QasmSimulator()
                            sim_run = simu.run(circuit_qasm, shots=1024)
                            sim_res = sim_run.result()
                            sim_counts = sim_res.data()['counts']
                            self.dp('quantum data', f'counts={sim_counts}')
                        else:
                            self.dp('quantum data', f'something else! (pass)')
                    elif len(args_type) == 2:
                        self.dp('token', f'call qsymbol | len args_type == 2')
                    else:
                        self.dp('token', f'call qsymbol | len args_type > 2')
            else:
                res = stats['args']
                args = self.resolve_args(res, stats)
                res = self.btin_funcs[code.value](*args)

        elif stats['obj'] == Tests:
            self.dp('token', 'obj=tests')

        elif stats['obj'] == TypeExpr:
            self.dp('token', f'obj=typeexpr | symbol={code.value}')
            if code.name.endswith('LITERAL'):
                stats['args'] += (
                    self.type_lookup[code.name](code),)  # (self.resolve_literal(code),)
                self.dp('token',
                        f'obj=typeexpr | args={stats["args"]} type args={type(stats["args"])}')
            elif code.name == 'SYMBOL':
                pass
            elif code.name == 'QSYMBOL':
                pass
            else:
                stats['args'] += self.resolve_args(code.value, stats)

        elif stats['obj'] == AttrAssign:
            # res = self.resolve_literal(code)
            if code.name.endswith('LITERAL'):
                res = self.type_lookup[code.name](code)
            else:
                res = None
            self.dp('token', f'attrassign res={res} type={type(res)}')
            stats['to_var'] += (res,)

        elif stats['obj'] == Caller:
            self.dp('token', f'obj=caller code={code.value}')
            # TODO: make it go to self.morpher and self.appender functions
            if stats['var'] and stats['type']:
                stats = self.op_rules.get(code.value, self.qsymbol_caller)(code, stats)
                """
                res = ()
                args = ()
                for k in stats['args']:
                    res += (k,)
                self.dp('token', f'caller={code.value} | stats={stats}')
                if len(stats['idx']) > 0:
                    for k0, k in enumerate(stats['idx']):
                        res2 = res
                        if code.name.endswith('GATE'):
                            res2 += (k,)
                        elif code.name == 'QSYMBOL':
                            if stats['type'] != 'circuit':
                                circuit_data = self.mem.read(scope=stats['scope'],
                                                             name=stats['func'],
                                                             var=code.value,
                                                             prop='data')
                                circuit_len = self.mem.read(scope=stats['scope'],
                                                            name=stats['func'],
                                                            var=code.value,
                                                            prop='len')
                                # print(self.mem)
                                # print(circuit_len)
                                circuit_qasm = self.circuit_to_qasm(circuit_data, circuit_len)
                                simu = QasmSimulator()
                                sim_run = simu.run(circuit_qasm, shots=1024)
                                sim_res = sim_run.result()
                                sim_counts = sim_res.data()['counts']
                                self.dp('quantum data', f'counts={sim_counts}')
                                if stats['type'] != 'measurement':
                                    if len(sim_counts) == 1:
                                        fin_res = int(list(sim_counts.keys())[0], 16)
                                        self.dp('quantum data', f'result={fin_res}')
                                        if code.value not in self.btin_funcs.keys():
                                            stats['args'] += (fin_res,)
                                        else:
                                            res2 += (fin_res,)
                                    else:
                                        pass
                                else:
                                    stats['idx'] += tuple(sim_counts.keys())
                                    stats['args'] += tuple(sim_counts.values())
                            else:
                                res2 += (self.mem.read(scope=stats['scope'],
                                                       name=stats['func'],
                                                       var=stats['var'],
                                                       index=k),)
                        else:
                            if stats['type'] not in ['hashmap', 'measurement']:
                                res2 += (self.mem.read(scope=stats['scope'],
                                                       name=stats['func'],
                                                       var=stats['var'],
                                                       index=k),)
                            else:
                                res2 = (self.mem.read(scope=stats['scope'],
                                                      name=stats['func'],
                                                      var=stats['var'],
                                                      index=k),)
                                # res2 += (self.mem.read(scope=stats['scope'],
                                #                        name=stats['func'],
                                #                        var=stats['var'],
                                #                        prop='data'),)
                        self.dp('token', f'res2 values={res2}')
                        btin_res = None
                        if code.value in self.btin_funcs.keys():

                            if code.name in ['CNOT_GATE', 'SWAP_GATE', 'CZ_GATE']:
                                args += self.resolve_args(res2, stats)
                                self.dp('token', f'obj=caller code={code.value} args={args}')
                                if len(args) == 2:
                                    self.dp('token', f'2-gate btin_func {code.value} {args}')
                                    btin_res = self.btin_funcs[code.value](*args)
                                    args = ()
                                    self.dp('token', f'2-gate btin_res={btin_res}')
                                    if btin_res:
                                        stats['to_var'] += (btin_res,)
                            elif code.name in ['TOFFOLI_GATE']:
                                args += self.resolve_args(res2, stats)
                                self.dp('token', f'obj=caller code={code.value} args={args}')
                                if len(args) == 3:
                                    btin_res = self.btin_funcs[code.value](*args)
                                    args = ()
                                    self.dp('token', f'3-gate btin_res={btin_res}')
                                    if btin_res:
                                        stats['to_var'] += (btin_res,)
                            else:
                                args = self.resolve_args(res2, stats)
                                if k0 + 1 < len(stats['idx']):
                                    btin_res = self.btin_funcs[code.value](*args, buffer=True)
                                else:
                                    btin_res = self.btin_funcs[code.value](*args, buffer=False)
                                self.dp('token', f'btin_res={btin_res}')
                                if btin_res:
                                    stats['to_var'] += (btin_res,)
                else:
                    if stats['type'] == 'hashmap':
                        pass
                    elif stats['type'] == 'measurement':
                        if code.name == 'QSYMBOL':
                            circuit_data = self.mem.read(scope=stats['scope'],
                                                         name=stats['func'],
                                                         var=code.value,
                                                         prop='data')
                            circuit_len = self.mem.read(scope=stats['scope'],
                                                        name=stats['func'],
                                                        var=code.value,
                                                        prop='len')
                            # print(self.mem)
                            # print(circuit_len)
                            circuit_qasm = self.circuit_to_qasm(circuit_data, circuit_len)
                            simu = QasmSimulator()
                            sim_run = simu.run(circuit_qasm, shots=1024)
                            sim_res = sim_run.result()
                            sim_counts = sim_res.data()['counts']
                            self.dp('quantum data', f'counts={sim_counts}')
                            stats['idx'] += tuple(sim_counts.keys())
                            stats['to_var'] += tuple(sim_counts.values())
                """
            else:
                if not stats['type']:
                    if not stats['var']:
                        res = self.resolve_args(stats['args'], stats)
                        self.dp('token', f'btin_func = {code.value}')
                        if code.value in self.btin_funcs.keys():
                            btin_res = self.btin_funcs[code.value](*stats['args'])
                            if btin_res is not None:
                                self.dp('token', f'btin_res={btin_res}')
                                if btin_res:
                                    pass
                                else:
                                    stats['skip'] += 1

                        elif code.value in ['int', 'float', 'str']:
                            self.dp('token', 'caller - int, float, str')
                        else:
                            self.dp('token', self.mem)
                            self.dp('token',
                                    self.mem.data[stats['scope']][stats['func']][code.value][
                                        'data'])
                            stats['args'] += self.mem.read(stats['scope'], stats['func'],
                                                           code.value)
                            self.dp('token', f'else={stats}')
                    else:
                        self.dp('token', 'no type... assigning')
                        stats['type'] = code.value
                        res = self.resolve_args(stats['args'], stats)
                        if code.value in self.btin_funcs.keys():
                            btin_res = self.btin_funcs[code.value](*stats['args'])
                            if stats['var'] and stats['type'] and btin_res:
                                stats['to_var'] += (res,)

        else:
            print(f'token, obj={stats["obj"]}')
        return stats

    # MORPHER AND APPENDER FUNCTIONS

    def morpher(self, code, stats):
        self.dp('morpher', f'caller={code.value} | stats={stats}')
        for k0, k in enumerate(stats['idx']):
            res2 = stats['args']
            res2 += (self.mem.read(scope=stats['scope'],
                                   name=stats['func'],
                                   var=stats['var'],
                                   index=k),)
            self.dp('morpher', f'res2 value={res2}')
            btin_res = None
            if code.value in self.btin_funcs.keys():
                args = self.resolve_args(res2, stats)
                if k0 + 1 < len(stats['idx']):
                    btin_res = self.btin_funcs[code.value](*args, buffer=True)
                else:
                    btin_res = self.btin_funcs[code.value](*args, buffer=False)
                self.dp('morpher', f'btin_res={btin_res}')
                if btin_res:
                    stats['to_var'] += (btin_res,)
        return stats

    def appender(self, code, stats):
        self.dp('appender', f'caller={code.value} | stats={stats}')
        if len(stats['idx']) > 0:
            if code.value in self.btin_funcs.keys():
                if code.name in ['CNOT_GATE', 'SWAP_GATE', 'CZ_GATE']:
                    if len(stats['args']) == len(stats['idx']) and stats['args'] % 2 == 0:
                        for arg, idx in zip(stats['args'], stats['idx']):
                            self.dp('appender', f'2-gate {code.value} ({arg}, {idx})')
                            btin_res = self.btin_funcs[code.value](arg, idx)
                            if btin_res:
                                stats['to_var'] += (btin_res,)
                    else:
                        if len(stats['args']) > 0:
                            for arg in stats['args']:
                                for idx in stats['idx']:
                                    if arg != idx:
                                        self.dp('appender', f'2-gate {code.value} ({arg}, {idx})')
                                        btin_res = self.btin_funcs[code.value](stats['args'], idx)
                                        if btin_res:
                                            stats['to_var'] += (btin_res,)
                        else:
                            if len(stats['idx']) % 2 == 0:
                                idxs = ()
                                for idx in stats['idx']:
                                    if len(idxs) < 2:
                                        idxs += (idx,)
                                    if len(idxs) == 2:
                                        self.dp('appender', f'2-gate {code.value} {idxs}')
                                        btin_res = self.btin_funcs[code.value](*idxs)
                                        if btin_res:
                                            stats['to_var'] += (btin_res,)
                                        idxs = ()
                elif code.name in ['TOFFOLI_GATE']:
                    if len(stats['idx']) % 3 == 0:
                        idxs = ()
                        for idx in stats['idx']:
                            if len(idxs) < 3:
                                idxs += (idx,)
                            if len(idxs) == 3:
                                self.dp('appender', f'3-gate {code.value} {idxs}')
                                btin_res = self.btin_funcs[code.value](*idxs)
                                if btin_res:
                                    stats['to_var'] += (btin_res,)
                    else:
                        if len(stats['args']) % 2 == 0:
                            args = ()
                            for arg in stats['args']:
                                if len(args) < 2:
                                    args += (arg,)
                                else:
                                    new_args = args
                                    for idx in stats['idx']:
                                        if len(new_args) == 2:
                                            new_args += (idx,)
                                        if arg not in idx and len(new_args) == 3:
                                            self.dp('appender', f'3-gate {code.value} {new_args}')
                                            btin_res = self.btin_funcs[code.value](*new_args)
                                            self.dp('nuller', f'btin_res={btin_res}')
                                            if btin_res:
                                                stats['to_var'] += (btin_res,)
                                            new_args = ()
                else:
                    args = self.resolve_args(stats['idx'], stats)
                    args += stats['args']
                    btin_res = self.btin_funcs[code.value](*args)
                    if btin_res:
                        stats['to_var'] += (btin_res,)
        else:
            self.dp('appender', 'len idx ==0')
        self.dp('appender', f'output stats={stats}')
        return stats

    def nuller(self, code, stats):
        self.dp('nuller', f'caller={code.value} | stats={stats}')
        for k0, idx in enumerate(stats['idx']):
            res = stats['args']
            if stats['type'] not in ['hashmap', 'measurement']:
                res += (self.mem.read(scope=stats['scope'],
                                      name=stats['func'],
                                      var=stats['var'],
                                      index=idx),)
            else:
                res += (self.mem.read(scope=stats['scope'],
                                      name=stats['func'],
                                      var=stats['var'],
                                      index=idx),)
            if code.value in self.btin_funcs.keys():
                args = self.resolve_args(res, stats)
                if k0 + 1 < len(stats['idx']):
                    btin_res = self.btin_funcs[code.value](*args, buffer=True)
                else:
                    btin_res = self.btin_funcs[code.value](*args, buffer=False)
                self.dp('nuller', f'btin_res={btin_res}')
                if btin_res:
                    stats['to_var'] += (btin_res,)
        return stats

    def qsymbol_caller(self, code, stats):
        self.dp('qsymbol-caller', f'caller={code.value} | stats={stats}')
        if stats['type'] == 'circuit':
            for k in stats['idx']:
                res = stats['args']
                res += (self.mem.read(scope=stats['scope'],
                                      name=stats['func'],
                                      var=stats['var'],
                                      index=k),)
                stats['args'] += (res,)
        else:
            if code.name == 'QSYMBOL':
                if stats['type'] != 'circuit':
                    circuit_data = self.mem.read(scope=stats['scope'],
                                                 name=stats['func'],
                                                 var=code.value,
                                                 prop='data')
                    circuit_len = self.mem.read(scope=stats['scope'],
                                                name=stats['func'],
                                                var=code.value,
                                                prop='len')
                    circuit_qasm = self.circuit_to_qasm(circuit_data, circuit_len)
                    simu = QasmSimulator()
                    sim_run = simu.run(circuit_qasm, shots=2048)
                    sim_res = sim_run.result()
                    sim_counts = sim_res.data()['counts']
                    self.dp('quantum data', f'counts={sim_counts}')
                    if stats['type'] != 'measurement':
                        if stats['type'] == 'hashmap':
                            raise ValueError(
                                f"Use measurement type instead of hashmap for circuits.")

                        if len(sim_counts) == 1:
                            fin_res = int(list(sim_counts.keys())[0], 16)
                            self.dp('quantum data', f'result={fin_res}')
                            stats['args'] += (fin_res,)
                        else:
                            self.interpret_qdata(sim_counts, stats['type'])
                    else:
                        stats['idx'] += tuple(sim_counts.keys())
                        stats['to_var'] += tuple(sim_counts.values())
                        self.dp('qsymbol-caller', f'meas data=({stats["idx"]}, {stats["to_var"]})')
                else:
                    self.dp('qsymbol-caller', f'appending {code.value} to var {stats["var"]}')
                    stats['to_var'] = (self.mem.read(scope=stats['scope'],
                                                     name=stats['func'],
                                                     var=code.value,
                                                     prop='data'),)
            else:
                self.dp('qsymbol-caller', f'No qsymbol: {code.value}')
        return stats

    # QUANTUM DATA COMPUTING

    def interpret_circuit(self, data):
        circuit_code = ""
        for node in data.nodes.data():
            if 'data' in node[1].keys():
                circuit_code += f"{self.trans_gates[node[1]['data']]} q[{node[0]}];\n"
        for edge in data.edges.data():
            if 'data' in edge[-1].keys():
                circuit_code += f"{self.trans_gates[edge[-1]['data']]}"
                for k0, k in enumerate(range(len(edge) - 1)):
                    circuit_code += f" q[{edge[k]}]"
                    if k0 + 2 < len(edge):
                        circuit_code += ", "
                circuit_code += ";\n"
        return circuit_code

    def circuit_to_qasm(self, data, data_len):
        circuit_code = """OPENQASM 2.0;\ninclude "qelib1.inc";\n"""
        circuit_code += f"qreg q[{data_len}];\ncreg c[{data_len}];\n\n"
        for k in data:
            circuit_code += self.interpret_circuit(k)
        circuit_code += "\nmeasure q -> c;\n"
        self.dp('qasm', f'file=\n\"{circuit_code}\"')
        qc = QuantumCircuit.from_qasm_str(circuit_code)
        return qc

    def interpret_qdata(self, data, data_type='int'):
        total_counts = 0
        final_value = 0
        for k, v in data.items():
            final_value += int(k, 16) * v
            total_counts += v
        final_value /= total_counts
        if data_type == 'int':
            return int(final_value)
        if data_type == 'str':
            return chr(int(final_value))
        if data_type == 'float':
            return final_value
        raise ValueError(f"No algorithm found for '{data_type}' process of quantum data.")

    # RESOLVING FUNCTIONS

    def resolve_literal(self, code):
        if isinstance(code, Token):
            if code.name.endswith('LITERAL'):
                return ast.literal_eval(code.value)
            return code.value
        return code

    def resolve_args(self, code, stats):
        if isinstance(code, tuple):
            args = ()
            for k in code:
                if isinstance(k, (int, float, str)):
                    args += (k,)
                elif isinstance(k, tuple):
                    new_args = self.resolve_args(k, stats)
                    args += (new_args,)
                elif isinstance(k, nx.DiGraph):
                    args += (k,)
                elif isinstance(k, Token):
                    new_args = ()
                    for p in stats['idx']:
                        new_args += (self.mem.read(stats['scope'], stats['func'], stats['var'], p),)
                    if new_args:
                        args += (new_args,)
                elif isinstance(k, dict):
                    args += tuple(f'{p[0]}:{p[1]}' for p in k.items())
            return args
        if isinstance(code, list):
            args = ()
            for k in code:
                if isinstance(k, (nx.Graph, int)):
                    args += (k,)
            return args
        if isinstance(code, str):
            return code,

    # FIRST WALK

    def walk(self, code, stats=None):
        if stats is None:
            stats = {'type': None,
                     'var': None,
                     'func': None,
                     'scope': None,
                     'key': None,
                     'obj': None,
                     'level': 0,
                     'skip': 0,
                     'args': (),
                     'idx': (),
                     'to_var': (),
                     'from_var': ()}
        stats = self.tasks[type(code)](code, stats)
        return stats


class GenAST:
    def __init__(self, code=None):
        self.code = SAMPLE_CODE_2 if code is None else code
        self.lc = lexer.lex(self.code)
        self.pc = parser.parse(self.lc)
        self.st = self.pc.symbolic.table

    def get_ast(self):
        return self.pc


class Code:
    """
    Execution the code from text to evaluation/interpreting code
    """

    def __init__(self, code, debug=False):
        self.code = code
        self.debug = debug
        self.lex_code = self.lex()
        self.parsed_code = self.parse()
        self.mem = None

    def lex(self, code=None):
        """
        Provides the tokens sequence for the given code.

        Returns
        -------
        iterable containing the tokens
        """
        code = self.code if code is None else code
        lex_code = lexer.lex(code)
        return lex_code

    def parse(self, lcode=None):
        """
        Parse the data, structuring the tokens into data.

        Returns
        -------
        tuple of dictionaries, tuples and tokens
        """
        lcode = self.lex_code if lcode is None else lcode
        lex_code = deepcopy(lcode)
        parse_code = parser.parse(lex_code)
        parsed_code = parse_code.symbolic.table
        return parsed_code

    def eval(self, pcode=None, keep=True):
        """
        Evaluate the intermediate representation code
        and execute the code
        """
        ev = Eval(debug=self.debug)
        pcode = self.parsed_code if pcode is None else pcode
        ev.walk(pcode)
        if keep:
            self.mem = ev.mem
        else:
            del ev.mem

    def run(self):
        """
        Bundle function to run all the previous functions
        """
        self.eval()
