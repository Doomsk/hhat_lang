"""Mapping functions to OpenQASM 2.0 and 3.0"""
from functools import partial

from hhat_lang.builtins.function_tokens import QFnToken
from hhat_lang.quantum_languages.openqasm.openqasm2 import (
    QasmKeyword,
    oper_expr
)


builtin_quantum_fn_mapper = {
    "2.0": {
        QFnToken.SHUFFLE: partial(
            map,
            lambda n: oper_expr((QasmKeyword.HADAMARD_OPER,), (n,))
        ),
        QFnToken.SYNC: partial(
            map,
            lambda n: oper_expr((QasmKeyword.CNOT_OPER,), (n,))
        ),
    },
    "3.0": {

    }
}
