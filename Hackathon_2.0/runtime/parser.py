class ASTNode:
    pass

class Program(ASTNode):
    def __init__(self, body):
        self.body = body

class VariableDeclaration(ASTNode):
    def __init__(self, kind, declarations):
        self.kind = kind  # 'let', 'const', 'var'
        self.declarations = declarations

class VariableDeclarator(ASTNode):
    def __init__(self, id_pattern, init):
        self.id = id_pattern  # Identifier, ObjectPattern, ArrayPattern
        self.init = init

class Identifier(ASTNode):
    def __init__(self, name):
        self.name = name

class Literal(ASTNode):
    def __init__(self, value):
        self.value = value

class TemplateLiteral(ASTNode):
    def __init__(self, quasis, expressions):
        self.quasis = quasis
        self.expressions = expressions

class BinaryExpression(ASTNode):
    def __init__(self, operator, left, right):
        self.operator = operator
        self.left = left
        self.right = right

class LogicalExpression(ASTNode):
    def __init__(self, operator, left, right):
        self.operator = operator
        self.left = left
        self.right = right

class UnaryExpression(ASTNode):
    def __init__(self, operator, argument, prefix=True):
        self.operator = operator
        self.argument = argument
        self.prefix = prefix

class UpdateExpression(ASTNode):
    def __init__(self, operator, argument, prefix):
        self.operator = operator
        self.argument = argument
        self.prefix = prefix

class AssignmentExpression(ASTNode):
    def __init__(self, operator, left, right):
        self.operator = operator
        self.left = left
        self.right = right

class MemberExpression(ASTNode):
    def __init__(self, object_, property_, computed, optional=False):
        self.object = object_
        self.property = property_
        self.computed = computed
        self.optional = optional

class CallExpression(ASTNode):
    def __init__(self, callee, arguments, optional=False):
        self.callee = callee
        self.arguments = arguments
        self.optional = optional

class ArrayExpression(ASTNode):
    def __init__(self, elements):
        self.elements = elements  # expressions or SpreadElements

class SpreadElement(ASTNode):
    def __init__(self, argument):
        self.argument = argument

class ObjectExpression(ASTNode):
    def __init__(self, properties):
        self.properties = properties

class Property(ASTNode):
    def __init__(self, key, value, computed=False, shorthand=False):
        self.key = key
        self.value = value
        self.computed = computed
        self.shorthand = shorthand

class FunctionDeclaration(ASTNode):
    def __init__(self, id_, params, body):
        self.id = id_
        self.params = params  # List of param dicts
        self.body = body

class FunctionExpression(ASTNode):
    def __init__(self, id_, params, body):
        self.id = id_
        self.params = params
        self.body = body

class ArrowFunctionExpression(ASTNode):
    def __init__(self, params, body, expression=False):
        self.params = params
        self.body = body
        self.expression = expression

class BlockStatement(ASTNode):
    def __init__(self, body):
        self.body = body

class ReturnStatement(ASTNode):
    def __init__(self, argument):
        self.argument = argument

class IfStatement(ASTNode):
    def __init__(self, test, consequent, alternate):
        self.test = test
        self.consequent = consequent
        self.alternate = alternate

class SwitchStatement(ASTNode):
    def __init__(self, discriminant, cases):
        self.discriminant = discriminant
        self.cases = cases

class SwitchCase(ASTNode):
    def __init__(self, test, consequent):
        self.test = test  # None for default
        self.consequent = consequent

class BreakStatement(ASTNode):
    pass

class ContinueStatement(ASTNode):
    pass

class ForStatement(ASTNode):
    def __init__(self, init, test, update, body):
        self.init = init
        self.test = test
        self.update = update
        self.body = body

class ForOfStatement(ASTNode):
    def __init__(self, left, right, body):
        self.left = left
        self.right = right
        self.body = body

class ForInStatement(ASTNode):
    def __init__(self, left, right, body):
        self.left = left
        self.right = right
        self.body = body

class WhileStatement(ASTNode):
    def __init__(self, test, body):
        self.test = test
        self.body = body

class DoWhileStatement(ASTNode):
    def __init__(self, body, test):
        self.body = body
        self.test = test

class ConditionalExpression(ASTNode):
    def __init__(self, test, consequent, alternate):
        self.test = test
        self.consequent = consequent
        self.alternate = alternate

class NewExpression(ASTNode):
    def __init__(self, callee, arguments):
        self.callee = callee
        self.arguments = arguments

class ObjectPattern(ASTNode):
    def __init__(self, properties):
        self.properties = properties

class ArrayPattern(ASTNode):
    def __init__(self, elements):
        self.elements = elements  # list of patterns


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def parse(self):
        body = []
        while not self.is_at_end():
            body.append(self.declaration())
        return Program(body)

    # ----------------- Helper Methods -----------------
    def is_at_end(self):
        return self.peek().type == "EOF"

    def peek(self):
        return self.tokens[self.current]

    def peek_next(self):
        if self.current + 1 >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.current + 1]

    def previous(self):
        return self.tokens[self.current - 1]

    def advance(self):
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def check(self, type_):
        if self.is_at_end():
            return False
        return self.peek().type == type_

    def match(self, *types):
        for type_ in types:
            if self.check(type_):
                self.advance()
                return True
        return False

    def consume(self, type_, err_msg):
        if self.check(type_):
            return self.advance()
        raise SyntaxError(f"{err_msg} at line {self.peek().line}:{self.peek().col}")

    # ----------------- Grammar Rules -----------------
    def declaration(self):
        if self.match("LET", "CONST", "VAR"):
            return self.var_declaration()
        if self.match("FUNCTION"):
            return self.function_declaration()
        return self.statement()

    def var_declaration(self):
        kind = self.previous().type.lower()
        declarations = []
        while True:
            id_pattern = self.parse_pattern()
            init = None
            if self.match("ASSIGN"):
                init = self.expression()
            declarations.append(VariableDeclarator(id_pattern, init))
            if not self.match("COMMA"):
                break
        self.match("SEMICOLON")  # optional
        return VariableDeclaration(kind, declarations)

    def parse_pattern(self):
        if self.match("LBRACKET"):
            elements = []
            while not self.check("RBRACKET"):
                if self.match("COMMA"):
                    elements.append(None)  # skipped element
                    continue
                if self.match("SPREAD"):
                    # rest element in array destructuring: [...rest]
                    inner = self.parse_pattern()
                    elements.append(SpreadElement(inner))
                    break
                pat = self.parse_pattern()
                # Support default: [a = 10]
                if self.match("ASSIGN"):
                    default_val = self.expression()
                    pat = AssignmentPattern(pat, default_val)
                elements.append(pat)
                if not self.check("RBRACKET"):
                    self.consume("COMMA", "Expected ',' or ']'")
            self.consume("RBRACKET", "Expected ']'")
            return ArrayPattern(elements)
        if self.match("LBRACE"):
            properties = []
            while not self.check("RBRACE"):
                # can be shorthand { x } or normal { x: y }
                # or computed { [key]: y }
                computed = False
                if self.match("LBRACKET"):
                    computed = True
                    key = self.expression()
                    self.consume("RBRACKET", "Expected ']'")
                    self.consume("COLON", "Expected ':'")
                    val = self.parse_pattern()
                    properties.append(Property(key, val, computed=True))
                else:
                    self.consume("IDENTIFIER", "Expected property name")
                    name_tok = self.previous()
                    key = Identifier(name_tok.value)
                    if self.match("COLON"):
                        val = self.parse_pattern()
                        # Support default: { x: y = default }
                        if self.match("ASSIGN"):
                            default_val = self.expression()
                            val = AssignmentPattern(val, default_val)
                        properties.append(Property(key, val, computed=False))
                    else:
                        # Shorthand with possible default: { x = default }
                        if self.match("ASSIGN"):
                            default_val = self.expression()
                            val = AssignmentPattern(key, default_val)
                            properties.append(Property(key, val, computed=False))
                        else:
                            properties.append(Property(key, key, computed=False, shorthand=True))
                if not self.check("RBRACE"):
                    self.consume("COMMA", "Expected ',' or '}'")
            self.consume("RBRACE", "Expected '}'")
            return ObjectPattern(properties)
        self.consume("IDENTIFIER", "Expected identifier in pattern")
        name = self.previous().value
        return Identifier(name)

    def function_declaration(self):
        self.consume("IDENTIFIER", "Expected function name")
        name = self.previous().value
        params = self.parse_parameters()
        self.consume("LBRACE", "Expected '{' for function body")
        body = self.block_statement()
        return FunctionDeclaration(Identifier(name), params, body)

    def parse_parameters(self):
        self.consume("LPAREN", "Expected '(' before parameters")
        params = []
        if not self.check("RPAREN"):
            while True:
                is_rest = False
                if self.match("SPREAD"):
                    is_rest = True
                self.consume("IDENTIFIER", "Expected parameter name")
                param_name = self.previous().value
                
                default_val = None
                if not is_rest and self.match("ASSIGN"):
                    default_val = self.expression()
                    
                params.append({
                    "name": param_name,
                    "is_rest": is_rest,
                    "default": default_val
                })
                
                if is_rest:
                    # Rest parameter must be last
                    if not self.check("RPAREN"):
                        raise SyntaxError("Rest parameter must be last")
                    break
                if not self.match("COMMA"):
                    break
        self.consume("RPAREN", "Expected ')' after parameters")
        return params

    def statement(self):
        if self.match("IF"):
            return self.if_statement()
        if self.match("SWITCH"):
            return self.switch_statement()
        if self.match("BREAK"):
            self.match("SEMICOLON")
            return BreakStatement()
        if self.match("CONTINUE"):
            self.match("SEMICOLON")
            return ContinueStatement()
        if self.match("RETURN"):
            return self.return_statement()
        if self.match("FOR"):
            return self.for_statement()
        if self.match("WHILE"):
            return self.while_statement()
        if self.match("DO"):
            return self.do_while_statement()
        if self.match("LBRACE"):
            return self.block_statement()
        return self.expression_statement()

    def if_statement(self):
        self.consume("LPAREN", "Expected '(' after if")
        test = self.expression()
        self.consume("RPAREN", "Expected ')' after condition")
        consequent = self.statement()
        alternate = None
        if self.match("ELSE"):
            alternate = self.statement()
        return IfStatement(test, consequent, alternate)

    def switch_statement(self):
        self.consume("LPAREN", "Expected '(' after switch")
        disc = self.expression()
        self.consume("RPAREN", "Expected ')' after switch value")
        self.consume("LBRACE", "Expected '{' before switch cases")
        cases = []
        while not self.check("RBRACE"):
            if self.match("CASE"):
                test = self.expression()
                self.consume("COLON", "Expected ':' after case value")
                consequent = []
                while not self.check("CASE") and not self.check("DEFAULT") and not self.check("RBRACE"):
                    consequent.append(self.statement())
                cases.append(SwitchCase(test, consequent))
            elif self.match("DEFAULT"):
                self.consume("COLON", "Expected ':' after default")
                consequent = []
                while not self.check("CASE") and not self.check("DEFAULT") and not self.check("RBRACE"):
                    consequent.append(self.statement())
                cases.append(SwitchCase(None, consequent))
            else:
                raise SyntaxError(f"Unexpected token in switch: {self.peek()}")
        self.consume("RBRACE", "Expected '}' after switch cases")
        return SwitchStatement(disc, cases)

    def return_statement(self):
        arg = None
        if not self.check("SEMICOLON") and self.peek().type != "RBRACE":
            arg = self.expression()
        self.match("SEMICOLON")
        return ReturnStatement(arg)

    def for_statement(self):
        self.consume("LPAREN", "Expected '(' after for")
        
        # Parse init / LHS
        init = None
        if self.match("LET", "CONST", "VAR"):
            # Could be let x of arr OR let i = 0
            kind = self.previous().type.lower()
            declarations = []
            id_pattern = self.parse_pattern()
            
            # check if of/in loop
            if self.match("OF", "IN"):
                is_of = self.previous().type == "OF"
                right = self.expression()
                self.consume("RPAREN", "Expected ')'")
                body = self.statement()
                decl = VariableDeclaration(kind, [VariableDeclarator(id_pattern, None)])
                if is_of:
                    return ForOfStatement(decl, right, body)
                else:
                    return ForInStatement(decl, right, body)
            
            # normal loop init
            init_val = None
            if self.match("ASSIGN"):
                init_val = self.expression()
            declarations.append(VariableDeclarator(id_pattern, init_val))
            while self.match("COMMA"):
                id_pat = self.parse_pattern()
                init_v = None
                if self.match("ASSIGN"):
                    init_v = self.expression()
                declarations.append(VariableDeclarator(id_pat, init_v))
            init = VariableDeclaration(kind, declarations)
        elif not self.check("SEMICOLON"):
            init = self.expression()
            if self.match("OF", "IN"):
                is_of = self.previous().type == "OF"
                right = self.expression()
                self.consume("RPAREN", "Expected ')'")
                body = self.statement()
                if is_of:
                    return ForOfStatement(init, right, body)
                else:
                    return ForInStatement(init, right, body)

        self.consume("SEMICOLON", "Expected ';'")
        
        test = None
        if not self.check("SEMICOLON"):
            test = self.expression()
        self.consume("SEMICOLON", "Expected ';'")
        
        update = None
        if not self.check("RPAREN"):
            update = self.expression()
        self.consume("RPAREN", "Expected ')'")
        
        body = self.statement()
        return ForStatement(init, test, update, body)

    def while_statement(self):
        self.consume("LPAREN", "Expected '(' after while")
        test = self.expression()
        self.consume("RPAREN", "Expected ')' after condition")
        body = self.statement()
        return WhileStatement(test, body)

    def do_while_statement(self):
        body = self.statement()
        self.consume("WHILE", "Expected 'while'")
        self.consume("LPAREN", "Expected '(' after while")
        test = self.expression()
        self.consume("RPAREN", "Expected ')'")
        self.match("SEMICOLON")
        return DoWhileStatement(body, test)

    def block_statement(self):
        body = []
        while not self.check("RBRACE") and not self.is_at_end():
            body.append(self.declaration())
        self.consume("RBRACE", "Expected '}'")
        return BlockStatement(body)

    def expression_statement(self):
        expr = self.expression()
        self.match("SEMICOLON")
        return expr

    # ----------------- Expressions -----------------
    def expression(self):
        return self.assignment()

    def assignment(self):
        expr = self.ternary()
        if self.match("ASSIGN", "ADD_ASSIGN", "SUB_ASSIGN", "MUL_ASSIGN", "DIV_ASSIGN", "MOD_ASSIGN", "EXP_ASSIGN"):
            op_tok = self.previous()
            right = self.assignment()
            return AssignmentExpression(op_tok.value, expr, right)
        return expr

    def ternary(self):
        expr = self.logical_or()
        if self.match("QUESTION"):
            consequent = self.expression()
            self.consume("COLON", "Expected ':' in ternary")
            alternate = self.assignment()
            return ConditionalExpression(expr, consequent, alternate)
        return expr

    def logical_or(self):
        expr = self.logical_and()
        while self.match("OR", "NULLISH"):
            op = self.previous().value
            right = self.logical_and()
            expr = LogicalExpression(op, expr, right)
        return expr

    def logical_and(self):
        expr = self.equality()
        while self.match("AND"):
            op = self.previous().value
            right = self.equality()
            expr = LogicalExpression(op, expr, right)
        return expr

    def equality(self):
        expr = self.comparison()
        while self.match("STRICT_EQUAL", "STRICT_NOT_EQUAL", "EQUAL", "NOT_EQUAL"):
            op = self.previous().value
            right = self.comparison()
            expr = BinaryExpression(op, expr, right)
        return expr

    def comparison(self):
        expr = self.additive()
        while self.match("LESS", "LESS_EQUAL", "GREATER", "GREATER_EQUAL", "IN"):
            op = self.previous().value
            right = self.additive()
            expr = BinaryExpression(op, expr, right)
        return expr

    def additive(self):
        expr = self.multiplicative()
        while self.match("PLUS", "MINUS"):
            op = self.previous().value
            right = self.multiplicative()
            expr = BinaryExpression(op, expr, right)
        return expr

    def multiplicative(self):
        expr = self.exponentiation()
        while self.match("STAR", "SLASH", "PERCENT"):
            op = self.previous().value
            right = self.exponentiation()
            expr = BinaryExpression(op, expr, right)
        return expr

    def exponentiation(self):
        expr = self.unary()
        while self.match("EXPONENT"):
            op = self.previous().value
            right = self.exponentiation()  # right associative
            expr = BinaryExpression(op, expr, right)
        return expr

    def unary(self):
        if self.match("BANG", "TYPEOF", "MINUS", "PLUS", "INCREMENT", "DECREMENT", "VOID", "DELETE"):
            op = self.previous()
            arg = self.unary()
            if op.type in ("INCREMENT", "DECREMENT"):
                return UpdateExpression(op.value, arg, prefix=True)
            return UnaryExpression(op.value, arg, prefix=True)
        return self.call_member_new()

    def call_member_new(self):
        if self.match("NEW"):
            callee = self.call_member_new()
            args = []
            if self.match("LPAREN"):
                args = self.parse_arguments()
            return NewExpression(callee, args)
        
        # postfix/member expressions
        expr = self.primary()
        while True:
            if self.match("DOT"):
                self.consume("IDENTIFIER", "Expected property name after '.'")
                prop = Identifier(self.previous().value)
                expr = MemberExpression(expr, prop, computed=False)
            elif self.match("OPTIONAL_CHAIN"):
                if self.match("LPAREN"):
                    args = self.parse_arguments()
                    expr = CallExpression(expr, args, optional=True)
                else:
                    self.consume("IDENTIFIER", "Expected property name after '?.'")
                    prop = Identifier(self.previous().value)
                    expr = MemberExpression(expr, prop, computed=False, optional=True)
            elif self.match("LBRACKET"):
                prop = self.expression()
                self.consume("RBRACKET", "Expected ']' after bracket index")
                expr = MemberExpression(expr, prop, computed=True)
            elif self.match("LPAREN"):
                args = self.parse_arguments()
                expr = CallExpression(expr, args)
            elif self.match("INCREMENT"):
                expr = UpdateExpression("++", expr, prefix=False)
            elif self.match("DECREMENT"):
                expr = UpdateExpression("--", expr, prefix=False)
            else:
                break
        return expr

    def parse_arguments(self):
        args = []
        if not self.check("RPAREN"):
            while True:
                if self.match("SPREAD"):
                    arg = self.expression()
                    args.append(SpreadElement(arg))
                else:
                    args.append(self.expression())
                if not self.match("COMMA"):
                    break
        self.consume("RPAREN", "Expected ')' after arguments")
        return args

    def primary(self):
        if self.is_arrow_function():
            return self.parse_arrow_function()

        if self.match("FALSE"): return Literal(False)
        if self.match("TRUE"): return Literal(True)
        if self.match("NULL"): return Literal(None)
        if self.match("UNDEFINED"): return Identifier("undefined")
        if self.match("NUMBER", "STRING"): return Literal(self.previous().value)
        if self.match("IDENTIFIER"): return Identifier(self.previous().value)

        # Template literals
        if self.match("TEMPLATE_LITERAL"):
            return TemplateLiteral([self.previous().value], [])
        if self.match("TEMPLATE_HEAD"):
            quasis = [self.previous().value]
            expressions = []
            while True:
                expressions.append(self.expression())
                if self.match("TEMPLATE_MIDDLE"):
                    quasis.append(self.previous().value)
                elif self.match("TEMPLATE_TAIL"):
                    quasis.append(self.previous().value)
                    break
                else:
                    raise SyntaxError("Unterminated template literal expression")
            return TemplateLiteral(quasis, expressions)

        # Array expression
        if self.match("LBRACKET"):
            elements = []
            if not self.check("RBRACKET"):
                while True:
                    if self.match("SPREAD"):
                        arg = self.expression()
                        elements.append(SpreadElement(arg))
                    else:
                        elements.append(self.expression())
                    if not self.match("COMMA"):
                        break
            self.consume("RBRACKET", "Expected ']' after array elements")
            return ArrayExpression(elements)

        # Object expression
        if self.match("LBRACE"):
            properties = []
            if not self.check("RBRACE"):
                while True:
                    computed = False
                    if self.match("LBRACKET"):
                        computed = True
                        key = self.expression()
                        self.consume("RBRACKET", "Expected ']'")
                        self.consume("COLON", "Expected ':'")
                        val = self.expression()
                        properties.append(Property(key, val, computed=True))
                    else:
                        # Ident, String, Number
                        if self.match("IDENTIFIER", "STRING", "NUMBER"):
                            key_tok = self.previous()
                            # check shorthand
                            if key_tok.type == "IDENTIFIER" and not self.check("COLON"):
                                key = Identifier(key_tok.value)
                                properties.append(Property(key, key, computed=False, shorthand=True))
                            else:
                                self.consume("COLON", "Expected ':'")
                                val = self.expression()
                                key = Identifier(key_tok.value) if key_tok.type == "IDENTIFIER" else Literal(key_tok.value)
                                properties.append(Property(key, val, computed=False))
                        else:
                            raise SyntaxError(f"Unexpected token in object: {self.peek()}")
                    if not self.match("COMMA"):
                        break
            self.consume("RBRACE", "Expected '}' after object properties")
            return ObjectExpression(properties)

        # Parenthesized expression
        if self.match("LPAREN"):
            expr = self.expression()
            self.consume("RPAREN", "Expected ')' after parenthesized expression")
            return expr

        # Function expression
        if self.match("FUNCTION"):
            name = None
            if self.match("IDENTIFIER"):
                name = self.previous().value
            params = self.parse_parameters()
            self.consume("LBRACE", "Expected '{'")
            body = self.block_statement()
            return FunctionExpression(Identifier(name) if name else None, params, body)

        raise SyntaxError(f"Expected expression but found {self.peek()}")

    def is_arrow_function(self):
        # x => ...
        if self.check("IDENTIFIER") and self.peek_next().type == "ARROW":
            return True
        # (params) => ...
        if self.check("LPAREN"):
            depth = 0
            i = self.current
            while i < len(self.tokens):
                tok = self.tokens[i]
                if tok.type == "LPAREN":
                    depth += 1
                elif tok.type == "RPAREN":
                    depth -= 1
                    if depth == 0:
                        if i + 1 < len(self.tokens) and self.tokens[i+1].type == "ARROW":
                            return True
                        break
                i += 1
        return False

    def parse_arrow_function(self):
        params = []
        if self.match("LPAREN"):
            if not self.check("RPAREN"):
                while True:
                    is_rest = False
                    if self.match("SPREAD"):
                        is_rest = True
                    # Support destructuring patterns in arrow fn params
                    if not is_rest and (self.check("LBRACKET") or self.check("LBRACE")):
                        # destructured parameter
                        pat = self.parse_pattern()
                        params.append({
                            "name": None,
                            "is_rest": False,
                            "default": None,
                            "pattern": pat
                        })
                    else:
                        self.consume("IDENTIFIER", "Expected parameter name")
                        name = self.previous().value
                        default_v = None
                        if not is_rest and self.match("ASSIGN"):
                            default_v = self.expression()
                        params.append({
                            "name": name,
                            "is_rest": is_rest,
                            "default": default_v
                        })
                    if is_rest:
                        break
                    if not self.match("COMMA"):
                        break
            self.consume("RPAREN", "Expected ')'")
        else:
            self.consume("IDENTIFIER", "Expected identifier")
            params.append({
                "name": self.previous().value,
                "is_rest": False,
                "default": None
            })
        self.consume("ARROW", "Expected '=>'")
        
        # Parse body
        if self.match("LBRACE"):
            body = self.block_statement()
            return ArrowFunctionExpression(params, body, expression=False)
        else:
            body = self.expression()
            return ArrowFunctionExpression(params, body, expression=True)
