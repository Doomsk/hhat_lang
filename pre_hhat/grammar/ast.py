"""AST"""
class AST:
    def __init__(self, name, *value):
        self.value = value
        self.name = name

    def __iter__(self):
        yield from self.value

    def __repr__(self):
        values = ', '.join([str(k) for k in self])
        return f"{self.name}({values})"
