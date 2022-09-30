"""Implement classical operators/functions"""

from .builtin import Operators

import pre_hhat.types as types


class Add(Operators):
    name = "ADD"

    def __call__(self, *args, **kwargs):
        if len(args) == 2:
            data_types = set(type(k) for k in args[0] + args[1])
            if len(data_types) == 1:
                res = ()
                if len(args[0]) == len(args[1]):
                    for k, v in zip(*args):
                        res += (k + v),
                elif len(args[0]) == 1:
                    for k in args[1]:
                        res += (args[0][0] + k),
                elif len(args[1]) == 1:
                    for k in args[0]:
                        res += (args[1][0] + k)
            if types.is_circuit(data_types):
                default = kwargs['value_type']().default
                res = kwargs["value_type"](default[0] if default else default)
                if len(args[0]) == len(args[1]):
                    # print('ARGS:', args[0], args[1])
                    for k, v in zip(*args):
                        if types.is_circuit(k) or types.is_circuit(v):
                            # print(f"* arg0: {k}\narg1: {v}")
                            add = k + (v, kwargs["stack"])
                            # print(f"* res add = {add} {type(add)}")
                            res += add
                        else:
                            add = k + v
                            res += add
                elif len(args[0]) == 1:
                    for k in args[1]:
                        if types.is_circuit(k) or types.is_circuit(args[0][0]):
                            add = args[0][0] + (k, kwargs["stack"])
                            res += add
                        else:
                            add = args[0][0] + k
                            res += add
                elif len(args[1]) == 1:
                    for k in args[0]:
                        if types.is_circuit(k) or types.is_circuit(args[1][0]):
                            add = args[1][0] + (k, kwargs["stack"])
                            res += add
                        else:
                            add = args[1][0] + k
                            res += add
            return kwargs.get("value_type", args[0][0].__class__)(*res)
        else:
            if len(set(type(k) for k in args)) == 1:
                res = types.ArrayNull()
                for k in args:
                    res = res + k
                res = (res if isinstance(res, tuple) else res,)
                return kwargs.get("value_type", args[0].__class__)(*res)
        raise NotImplementedError(f"{self.__class__.__name__}: not implemented summing different data.")


class Print(Operators):
    name = "PRINT"

    def __call__(self, *args, **kwargs):
        if "value_type" in kwargs.keys():
            kwargs.pop("value_type")
        if "stack" in kwargs.keys():
            kwargs.pop("stack")

        if len(args) == 2:
            args = args[0] + args[1]
        for n, k in enumerate(args):
            if not isinstance(k, types.SingleNull):
                k = str(k).strip('"').strip("'") if isinstance(k, types.SingleStr) else k
                if n < len(args) - 1:
                    print(k, end=" ")
                else:
                    print(k)
        return types.ArrayNull()
