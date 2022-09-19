"""Example of code."""

from time import process_time

from pre_hhat.interpreter.pre_evaluator import PreEvaluator
from pre_hhat.interpreter.evaluator import Evaluator, run
from pre_hhat.grammar.cst import parsing_code, examples


def example_run(debug=True, print_code=False, symboltable=True, interpreter=True):
    for k in examples:
        print("=" * 50)
        print("*  File:")
        print(f"      {k}")
        print()
        print()
        print("*  Code:")
        print()
        code_ast = parsing_code(k, print_code=print_code, debug=debug)
        print()
        print("*  AST:")
        print(f"      {code_ast}")
        pre_eval = PreEvaluator(code_ast)
        table = pre_eval.walk_tree()
        print()
        if symboltable:
            print()
            print("*  SymbolTable:")
            print(f"      {table}")
            print()
            if interpreter:
                print()
                print("*  Interpreter:")
                print("-" * 30)
                print()
                ev = Evaluator(table)
                t0 = process_time()
                ev.walk_tree()
                t1 = process_time()
                print()
                print("-" * 30)
                print(f"done in {round(t1-t0, 6)}s.")


if __name__ == "__main__":
    example_run(debug=False, print_code=True, interpreter=True)
