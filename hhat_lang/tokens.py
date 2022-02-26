
# define tokens
# insert new tokens in the end
tokens = dict()
tokens.update({"OPEN": r"\("})
tokens.update({"CLOSE": r"\)"})

tokens.update({"ASSIGN": r"=(?!\w)"})
tokens.update({"COLON": r":"})
tokens.update({"STAR": r"\*"})
tokens.update({"COMMA": r"\,"})

tokens.update({"IMPORTS": r"imports(?!\w)"})
tokens.update({"MAIN": r"main(?!\w)"})
tokens.update({"FUNCTION": r"func(?!\w)"})
tokens.update({"RETURN": r"return(?!\w)"})

tokens.update({"IF": r"if(?!\w)"})
tokens.update({"ELIF": r"elif(?!\w)"})
tokens.update({"ELSE": r"else(?!\w)"})

tokens.update({"AND": r"\+"})
tokens.update({"OR": r"\-"})
tokens.update({"NOT": r"not(?!\w)"})

tokens.update({"FOR": r"for(?!\w)"})
tokens.update({"IN": r"in(?!\w)"})
tokens.update({"RANGE": r"\.\."})
tokens.update({"AS": r"as(?!\w)"})

tokens.update({"EQ": r"=="})
tokens.update({"GT": r">"})
tokens.update({"LT": r"<"})
tokens.update({"GET": r">="})
tokens.update({"LET": r"<="})
tokens.update({"NEQ": r"!="})

tokens.update({"NULL_TYPE": r"null(?!\w)"})
tokens.update({"INTEGER_TYPE": r"int(?!\w)"})
tokens.update({"FLOAT_TYPE": r"float(?!\w)"})
tokens.update({"BOOL_TYPE": r"bool(?!\w)"})
tokens.update({"STRING_TYPE": r"str(?!\w)"})
tokens.update({"GATES_TYPE": r"circuit(?!\w)"})
tokens.update({"REGISTER_TYPE": r"register(?!\w)"})
tokens.update({"LIST_TYPE": r"list(?!\w)"})
tokens.update({"HASHMAP_TYPE": r"hashmap(?!\w)"})
tokens.update({"MEAS_TYPE": r"measurement(?!\w)"})

tokens.update({"TRUE": r"T(?!\w)"})
tokens.update({"FALSE": r"F(?!\w)"})

tokens.update({"H": r"@h(?!\w)"})
tokens.update({"X": r"@x(?!\w)"})
tokens.update({"Z": r"@z(?!\w)"})
tokens.update({"Y": r"@y(?!\w)"})
tokens.update({"CNOT": r"@cnot(?!\w)"})
tokens.update({"SWAP": r"@swap(?!\w)"})
tokens.update({"CZ": r"@cz(?!\w)"})
tokens.update({"RX": r"@rx(?!\w)"})
tokens.update({"RZ": r"@rz(?!\w)"})
tokens.update({"RY": r"@ry(?!\w)"})
tokens.update({"T": r"@t(?!\w)"})
tokens.update({"T_DAG": r"@tdag(?!\w)"})
tokens.update({"S": r"@s(?!\w)"})
tokens.update({"S_DAG": r"@sdag(?!\w)"})
tokens.update({"CR": r"@cr(?!\w)"})
tokens.update({"TOFFOLI": r"@toffoli(?!\w)"})

tokens.update({"SUPERPOSN": r"@superposn(?!\w)"})
tokens.update({"AMPLIFICATION": r"@ampl(?!\w)"})

tokens.update({"RESET": r"@reset(?!\w)"})
tokens.update({"MEASURE": r"@return(?!\w)"})

tokens.update({"ADD": r"add(?!\w)"})
tokens.update({"MULT": r"mult(?!\w)"})
tokens.update({"DIV": r"div(?!\w)"})
tokens.update({"POWER": r"power(?!\w)"})
tokens.update({"SQRT": r"sqrt(?!\w)"})
tokens.update({"INT_SQRT": r"int_sqrt(?!\w)"})
tokens.update({"LENGTH": r"len(?!\w)"})

tokens.update({"PRINT": r"print(?!\w)"})

tokens.update({"SYMBOL": r"[a-zA-Z_]+[a-zA-Z_0-9]*"})
tokens.update({"QSYMBOL": r"@[a-zA-Z_]+[a-zA-Z_0-9]*"})
tokens.update({"PSYMBOL": r"\?[a-zA-Z_]+"})
tokens.update({"DSYMBOL": r"\#[a-zA-Z_0-9\.\-]+"})

tokens.update({"INT_NUMBER": r"[-+]?[0-9]+"})
tokens.update({"FLOAT_NUMBER": r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?"})
# tokens.update({"IMAG_NUMBER": r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?j(?!\w)"})
tokens.update({"STRING": r"(\".*\")|(\'.*\')"})


# * insert new tokens below *
