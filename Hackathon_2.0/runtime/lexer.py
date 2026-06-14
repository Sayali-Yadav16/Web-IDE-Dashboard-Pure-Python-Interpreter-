class Token:
    def __init__(self, type_, value, line, col):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, {self.line}:{self.col})"


KEYWORDS = {
    "let": "LET",
    "const": "CONST",
    "var": "VAR",
    "function": "FUNCTION",
    "return": "RETURN",
    "if": "IF",
    "else": "ELSE",
    "switch": "SWITCH",
    "case": "CASE",
    "break": "BREAK",
    "continue": "CONTINUE",
    "default": "DEFAULT",
    "for": "FOR",
    "while": "WHILE",
    "do": "DO",
    "new": "NEW",
    "typeof": "TYPEOF",
    "in": "IN",
    "of": "OF",
    "true": "TRUE",
    "false": "FALSE",
    "null": "NULL",
    "undefined": "UNDEFINED"
}


class Lexer:
    def __init__(self, source):
        self.source = source
        self.tokens = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.col = 1
        self.template_brace_depths = []

    def scan_tokens(self):
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()
        self.tokens.append(Token("EOF", "", self.line, self.col))
        return self.tokens

    def is_at_end(self):
        return self.current >= len(self.source)

    def advance(self):
        char = self.source[self.current]
        self.current += 1
        self.col += 1
        return char

    def peek(self):
        if self.is_at_end():
            return "\0"
        return self.source[self.current]

    def peek_next(self):
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def match(self, expected):
        if self.is_at_end():
            return False
        if self.source[self.current] != expected:
            return False
        self.current += 1
        self.col += 1
        return True

    def scan_token(self):
        char = self.advance()

        # Whitespace
        if char in (" ", "\r", "\t"):
            return
        if char == "\n":
            self.line += 1
            self.col = 1
            return

        # Comments or Slash operator
        if char == "/":
            if self.match("/"):
                # Line comment
                while self.peek() != "\n" and not self.is_at_end():
                    self.advance()
            elif self.match("*"):
                # Block comment
                while not self.is_at_end():
                    if self.peek() == "\n":
                        self.line += 1
                        self.col = 1
                    if self.peek() == "*" and self.peek_next() == "/":
                        self.advance() # consume *
                        self.advance() # consume /
                        break
                    self.advance()
            elif self.match("="):
                self.add_token("DIV_ASSIGN", "/=")
            else:
                self.add_token("SLASH", "/")
            return

        # Strings (single or double quote)
        if char in ('"', "'"):
            self.scan_string(char)
            return

        # Template string (backtick)
        if char == "`":
            self.scan_template()
            return

        # Braces with interpolation tracking
        if char == "{":
            if self.template_brace_depths:
                self.template_brace_depths[-1] += 1
            self.add_token("LBRACE", "{")
            return

        if char == "}":
            if self.template_brace_depths and self.template_brace_depths[-1] == 0:
                # End of interpolation, resume template string!
                self.template_brace_depths.pop()
                self.scan_template(inside_interpolation=True)
            else:
                if self.template_brace_depths:
                    self.template_brace_depths[-1] -= 1
                self.add_token("RBRACE", "}")
            return

        # Simple characters / operators
        if char == "(": self.add_token("LPAREN", "("); return
        if char == ")": self.add_token("RPAREN", ")"); return
        if char == "[": self.add_token("LBRACKET", "["); return
        if char == "]": self.add_token("RBRACKET", "]"); return
        if char == ",": self.add_token("COMMA", ","); return
        if char == ";": self.add_token("SEMICOLON", ";"); return

        # Dot, Optional Chaining, Spread, or Number starting with dot
        if char == ".":
            if self.peek().isdigit():
                self.scan_number(starts_with_dot=True)
            elif self.peek() == "." and self.peek_next() == ".":
                self.advance() # consume second dot
                self.advance() # consume third dot
                self.add_token("SPREAD", "...")
            else:
                self.add_token("DOT", ".")
            return

        # Operators
        if char == "+":
            if self.match("+"): self.add_token("INCREMENT", "++")
            elif self.match("="): self.add_token("ADD_ASSIGN", "+=")
            else: self.add_token("PLUS", "+")
            return

        if char == "-":
            if self.match("-"): self.add_token("DECREMENT", "--")
            elif self.match("="): self.add_token("SUB_ASSIGN", "-=")
            else: self.add_token("MINUS", "-")
            return

        if char == "*":
            if self.match("*"):
                if self.match("="): self.add_token("EXP_ASSIGN", "**=")
                else: self.add_token("EXPONENT", "**")
            elif self.match("="): self.add_token("MUL_ASSIGN", "*=")
            else: self.add_token("STAR", "*")
            return

        if char == "%":
            if self.match("="): self.add_token("MOD_ASSIGN", "%=")
            else: self.add_token("PERCENT", "%")
            return

        if char == "=":
            if self.match("="):
                if self.match("="): self.add_token("STRICT_EQUAL", "===")
                else: self.add_token("EQUAL", "==")
            elif self.match(">"):
                self.add_token("ARROW", "=>")
            else:
                self.add_token("ASSIGN", "=")
            return

        if char == "!":
            if self.match("="):
                if self.match("="): self.add_token("STRICT_NOT_EQUAL", "!==")
                else: self.add_token("NOT_EQUAL", "!=")
            else:
                self.add_token("BANG", "!")
            return

        if char == "<":
            if self.match("="): self.add_token("LESS_EQUAL", "<=")
            else: self.add_token("LESS", "<")
            return

        if char == ">":
            if self.match("="): self.add_token("GREATER_EQUAL", ">=")
            else: self.add_token("GREATER", ">")
            return

        if char == "&":
            if self.match("&"): self.add_token("AND", "&&")
            else: raise SyntaxError(f"Unexpected token '&' on line {self.line}")
            return

        if char == "|":
            if self.match("|"): self.add_token("OR", "||")
            else: raise SyntaxError(f"Unexpected token '|' on line {self.line}")
            return

        if char == "?":
            if self.match("?"):
                self.add_token("NULLISH", "??")
            elif self.match("."):
                self.add_token("OPTIONAL_CHAIN", "?.")
            else:
                self.add_token("QUESTION", "?")
            return

        if char == ":":
            self.add_token("COLON", ":")
            return

        # Numbers
        if char.isdigit():
            self.scan_number()
            return

        # Identifiers / Keywords
        if char.isalpha() or char in ("_", "$"):
            self.scan_identifier()
            return

        raise SyntaxError(f"Unexpected character '{char}' on line {self.line}:{self.col-1}")

    def add_token(self, type_, value):
        self.tokens.append(Token(type_, value, self.line, self.col - len(str(value))))

    def scan_string(self, quote):
        content = []
        start_line = self.line
        start_col = self.col - 1

        while not self.is_at_end():
            char = self.peek()
            if char == quote:
                self.advance() # consume quote
                self.tokens.append(Token("STRING", "".join(content), start_line, start_col))
                return
            elif char == "\\":
                self.advance() # consume \
                if self.is_at_end():
                    raise SyntaxError(f"Unterminated string literal starting at line {start_line}")
                escaped = self.advance()
                if escaped == 'n': content.append('\n')
                elif escaped == 't': content.append('\t')
                elif escaped == 'r': content.append('\r')
                elif escaped == '"': content.append('"')
                elif escaped == "'": content.append("'")
                elif escaped == '\\': content.append('\\')
                else: content.append(escaped)
            elif char == "\n":
                # JS allows multi-line strings if backslash escaped, but plain multiline strings throw unless template literal
                raise SyntaxError(f"Unterminated string literal on line {self.line}")
            else:
                content.append(self.advance())

        raise SyntaxError(f"Unterminated string literal starting at line {start_line}")

    def scan_template(self, inside_interpolation=False):
        content = []
        start_line = self.line
        start_col = self.col - 1 if not inside_interpolation else self.col

        while not self.is_at_end():
            char = self.peek()
            if char == "`":
                self.advance() # consume `
                token_type = "TEMPLATE_TAIL" if inside_interpolation else "TEMPLATE_LITERAL"
                self.tokens.append(Token(token_type, "".join(content), start_line, start_col))
                return
            elif char == "$" and self.peek_next() == "{":
                self.advance() # consume $
                self.advance() # consume {
                token_type = "TEMPLATE_MIDDLE" if inside_interpolation else "TEMPLATE_HEAD"
                self.tokens.append(Token(token_type, "".join(content), start_line, start_col))
                self.template_brace_depths.append(0)
                return
            elif char == "\\":
                self.advance()
                if self.is_at_end():
                    raise SyntaxError(f"Unterminated template literal on line {self.line}")
                escaped = self.advance()
                if escaped == 'n': content.append('\n')
                elif escaped == 't': content.append('\t')
                elif escaped == 'r': content.append('\r')
                elif escaped == '`': content.append('`')
                elif escaped == '$': content.append('$')
                elif escaped == '\\': content.append('\\')
                else: content.append(escaped)
            elif char == "\n":
                content.append("\n")
                self.advance()
                self.line += 1
                self.col = 1
            else:
                content.append(self.advance())

        raise SyntaxError(f"Unterminated template literal starting at line {start_line}")

    def scan_number(self, starts_with_dot=False):
        start_line = self.line
        start_col = self.col - 1 if not starts_with_dot else self.col - 2
        
        # Check for hexadecimal
        if not starts_with_dot and self.source[self.current-1] == '0' and self.peek().lower() == 'x':
            self.advance() # consume 'x' or 'X'
            while self.peek().isalnum():
                self.advance()
            hex_str = self.source[self.start:self.current]
            try:
                val = float(int(hex_str, 16))
                self.tokens.append(Token("NUMBER", val, start_line, start_col))
            except ValueError:
                raise SyntaxError(f"Invalid hexadecimal literal on line {self.line}")
            return

        # Decimal number
        if starts_with_dot:
            # We already consumed '.'
            pass
            
        while self.peek().isdigit():
            self.advance()

        # Fractional part
        if not starts_with_dot and self.peek() == "." and self.peek_next().isdigit():
            self.advance() # consume '.'
            while self.peek().isdigit():
                self.advance()

        # Scientific notation
        if self.peek().lower() == 'e':
            self.advance() # consume 'e'
            if self.peek() in ('+', '-'):
                self.advance()
            if not self.peek().isdigit():
                raise SyntaxError(f"Invalid scientific notation exponent on line {self.line}")
            while self.peek().isdigit():
                self.advance()

        num_str = self.source[self.start:self.current]
        self.tokens.append(Token("NUMBER", float(num_str), start_line, start_col))

    def scan_identifier(self):
        while self.peek().isalnum() or self.peek() in ("_", "$"):
            self.advance()

        text = self.source[self.start:self.current]
        type_ = KEYWORDS.get(text, "IDENTIFIER")
        self.tokens.append(Token(type_, text, self.line, self.col - len(text)))
