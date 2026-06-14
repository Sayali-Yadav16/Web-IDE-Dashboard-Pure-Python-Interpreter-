class Environment:
    def __init__(self, outer=None):
        self.outer = outer
        self.records = {}
        self.constants = set()

    def declare(self, name, value, is_const=False):
        if name in self.records:
            raise SyntaxError(f"Identifier '{name}' has already been declared")
        self.records[name] = value
        if is_const:
            self.constants.add(name)

    def assign(self, name, value):
        if name in self.records:
            if name in self.constants:
                raise TypeError(f"Assignment to constant variable '{name}'")
            self.records[name] = value
            return
        if self.outer is not None:
            self.outer.assign(name, value)
            return
        raise ReferenceError(f"'{name}' is not defined")

    def get(self, name):
        if name in self.records:
            return self.records[name]
        if self.outer is not None:
            return self.outer.get(name)
        raise ReferenceError(f"'{name}' is not defined")
