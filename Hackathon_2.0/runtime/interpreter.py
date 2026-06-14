import math
from runtime.environment import Environment
from runtime.js_objects import (
    JSObject, JSArray, JSFunction, JSNativeFunction, UNDEFINED,
    js_to_string, js_to_boolean, js_to_number, interpreter_strict_equals
)
from runtime.js_builtins import setup_global_environment, get_string_property, get_number_property, JSDate
from runtime import parser

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class BreakException(Exception):
    pass

class ContinueException(Exception):
    pass

def js_loose_equals(a, b):
    if type(a) == type(b):
        return interpreter_strict_equals(a, b)
    if (a is None or a is UNDEFINED) and (b is None or b is UNDEFINED):
        return True
    if a is None or a is UNDEFINED or b is None or b is UNDEFINED:
        return False
    if isinstance(a, (int, float)) and isinstance(b, str):
        return a == js_to_number(b)
    if isinstance(a, str) and isinstance(b, (int, float)):
        return js_to_number(a) == b
    if isinstance(a, bool):
        return js_loose_equals(js_to_number(a), b)
    if isinstance(b, bool):
        return js_loose_equals(a, js_to_number(b))
    if isinstance(a, (JSObject, JSArray)) and isinstance(b, (str, int, float, bool)):
        return js_loose_equals(js_to_string(a), b)
    if isinstance(a, (str, int, float, bool)) and isinstance(b, (JSObject, JSArray)):
        return js_loose_equals(a, js_to_string(b))
    return a is b

class Interpreter:
    def __init__(self):
        self.globals = Environment()
        self.stdout_buffer = []
        setup_global_environment(self.globals)

    def interpret(self, program):
        try:
            self.evaluate(program, self.globals)
            return {
                "output": "\n".join(self.stdout_buffer),
                "error": None,
                "success": True
            }
        except Exception as e:
            # Format error name and message
            err_name = type(e).__name__
            err_msg = str(e)
            return {
                "output": "\n".join(self.stdout_buffer),
                "error": f"{err_name}: {err_msg}",
                "success": False
            }

    def evaluate(self, node, env):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, env)

    def generic_visit(self, node, env):
        raise NotImplementedError(f"No visit_{type(node).__name__} method defined")

    def visit_Program(self, node, env):
        for stmt in node.body:
            self.evaluate(stmt, env)
        return UNDEFINED

    # ----------------- Statements -----------------
    def visit_VariableDeclaration(self, node, env):
        for decl in node.declarations:
            val = UNDEFINED
            if decl.init is not None:
                val = self.evaluate(decl.init, env)
            
            # Use declare_pattern to handle destructuring and single variables
            self.declare_pattern(decl.id, val, env, is_const=(node.kind == 'const'))
        return UNDEFINED

    def declare_pattern(self, pattern, value, env, is_const):
        if isinstance(pattern, parser.Identifier):
            env.declare(pattern.name, value, is_const)
        elif isinstance(pattern, parser.ArrayPattern):
            if isinstance(value, JSArray):
                elements = value.elements
            elif isinstance(value, list):
                elements = value
            elif isinstance(value, str):
                elements = list(value)
            else:
                elements = []
                
            for i, subpat in enumerate(pattern.elements):
                if subpat is not None:
                    val = elements[i] if i < len(elements) else UNDEFINED
                    self.declare_pattern(subpat, val, env, is_const)
        elif isinstance(pattern, parser.ObjectPattern):
            for prop in pattern.properties:
                if prop.computed:
                    key = self.evaluate(prop.key, env)
                else:
                    key = prop.key.name
                    
                val = UNDEFINED
                if isinstance(value, JSObject):
                    val = value.get(key)
                    
                self.declare_pattern(prop.value, val, env, is_const)

    def visit_BlockStatement(self, node, env):
        block_env = Environment(env)
        self.execute_block(node.body, block_env)
        return UNDEFINED

    def execute_block(self, body, env):
        for stmt in body:
            self.evaluate(stmt, env)

    def visit_ReturnStatement(self, node, env):
        val = UNDEFINED
        if node.argument is not None:
            val = self.evaluate(node.argument, env)
        raise ReturnException(val)

    def visit_BreakStatement(self, node, env):
        raise BreakException()

    def visit_ContinueStatement(self, node, env):
        raise ContinueException()

    def visit_IfStatement(self, node, env):
        test_val = self.evaluate(node.test, env)
        if js_to_boolean(test_val):
            self.evaluate(node.consequent, env)
        elif node.alternate is not None:
            self.evaluate(node.alternate, env)
        return UNDEFINED

    def visit_SwitchStatement(self, node, env):
        disc_val = self.evaluate(node.discriminant, env)
        matched = False
        default_case = None
        
        # We need a loop to find match, and then execute all subsequent case bodies until a break!
        case_idx = -1
        for i, case in enumerate(node.cases):
            if case.test is None:
                default_case = i
                continue
            test_val = self.evaluate(case.test, env)
            if js_loose_equals(disc_val, test_val):
                matched = True
                case_idx = i
                break
                
        if not matched and default_case is not None:
            case_idx = default_case
            matched = True
            
        if matched:
            try:
                # fall-through behavior
                for i in range(case_idx, len(node.cases)):
                    for stmt in node.cases[i].consequent:
                        self.evaluate(stmt, env)
            except BreakException:
                pass
        return UNDEFINED

    def visit_WhileStatement(self, node, env):
        while js_to_boolean(self.evaluate(node.test, env)):
            try:
                self.evaluate(node.body, env)
            except BreakException:
                break
            except ContinueException:
                continue
        return UNDEFINED

    def visit_DoWhileStatement(self, node, env):
        while True:
            try:
                self.evaluate(node.body, env)
            except BreakException:
                break
            except ContinueException:
                pass
            if not js_to_boolean(self.evaluate(node.test, env)):
                break
        return UNDEFINED

    def visit_ForStatement(self, node, env):
        # Create a parent scope for the initializer (block scoping)
        loop_env = Environment(env)
        if node.init is not None:
            self.evaluate(node.init, loop_env)
            
        while True:
            if node.test is not None:
                test_val = self.evaluate(node.test, loop_env)
                if not js_to_boolean(test_val):
                    break
            
            # Each loop iteration body runs in its own environment
            body_env = Environment(loop_env)
            try:
                self.evaluate(node.body, body_env)
            except BreakException:
                break
            except ContinueException:
                pass
            
            # Evaluate update in loop scope
            if node.update is not None:
                self.evaluate(node.update, loop_env)
        return UNDEFINED

    def visit_ForOfStatement(self, node, env):
        right_val = self.evaluate(node.right, env)
        if isinstance(right_val, JSArray):
            items = right_val.elements
        elif isinstance(right_val, list):
            items = right_val
        elif isinstance(right_val, str):
            items = list(right_val)
        else:
            items = []
            
        for item in items:
            loop_env = Environment(env)
            if isinstance(node.left, parser.VariableDeclaration):
                self.declare_pattern(node.left.declarations[0].id, item, loop_env, is_const=(node.left.kind == 'const'))
            else:
                self.assign_pattern(node.left, item, loop_env)
                
            try:
                self.evaluate(node.body, loop_env)
            except BreakException:
                break
            except ContinueException:
                continue
        return UNDEFINED

    def visit_ForInStatement(self, node, env):
        right_val = self.evaluate(node.right, env)
        if isinstance(right_val, JSArray):
            keys = [float(i) for i in range(len(right_val.elements))]
        elif isinstance(right_val, JSObject):
            keys = list(right_val.properties.keys())
        elif isinstance(right_val, str):
            keys = [float(i) for i in range(len(right_val))]
        else:
            keys = []
            
        for key in keys:
            loop_env = Environment(env)
            if isinstance(node.left, parser.VariableDeclaration):
                self.declare_pattern(node.left.declarations[0].id, key, loop_env, is_const=(node.left.kind == 'const'))
            else:
                self.assign_pattern(node.left, key, loop_env)
                
            try:
                self.evaluate(node.body, loop_env)
            except BreakException:
                break
            except ContinueException:
                continue
        return UNDEFINED

    # ----------------- Expressions -----------------
    def visit_Literal(self, node, env):
        if node.value is None and self.stdout_buffer: # check if token undefined
            # Literal value parsing maps null to None, but we need to ensure correct output
            pass
        return node.value

    def visit_Identifier(self, node, env):
        if node.name == "undefined":
            return UNDEFINED
        return env.get(node.name)

    def visit_TemplateLiteral(self, node, env):
        result = []
        for i in range(len(node.quasis)):
            result.append(node.quasis[i])
            if i < len(node.expressions):
                expr_val = self.evaluate(node.expressions[i], env)
                result.append(js_to_string(expr_val))
        return "".join(result)

    def visit_BinaryExpression(self, node, env):
        left_val = self.evaluate(node.left, env)
        right_val = self.evaluate(node.right, env)
        
        op = node.operator
        if op == "+":
            # String concatenation if either is string
            if isinstance(left_val, str) or isinstance(right_val, str):
                return js_to_string(left_val) + js_to_string(right_val)
            return js_to_number(left_val) + js_to_number(right_val)
            
        if op == "-": return js_to_number(left_val) - js_to_number(right_val)
        if op == "*": return js_to_number(left_val) * js_to_number(right_val)
        if op == "/":
            denom = js_to_number(right_val)
            if denom == 0:
                return float('inf') if js_to_number(left_val) >= 0 else -float('inf')
            return js_to_number(left_val) / denom
        if op == "%":
            denom = js_to_number(right_val)
            if denom == 0:
                return float('nan')
            return math.fmod(js_to_number(left_val), denom)
        if op == "**": return js_to_number(left_val) ** js_to_number(right_val)
        
        # Comparators
        if op == "==": return js_loose_equals(left_val, right_val)
        if op == "!=": return not js_loose_equals(left_val, right_val)
        if op == "===": return interpreter_strict_equals(left_val, right_val)
        if op == "!==": return not interpreter_strict_equals(left_val, right_val)
        
        # Relational: JS spec uses numeric comparison unless both operands are strings
        if op in ("<", ">", "<=", ">="):
            if isinstance(left_val, str) and isinstance(right_val, str):
                # Lexicographic string comparison
                if op == "<":  return left_val < right_val
                if op == ">": return left_val > right_val
                if op == "<=": return left_val <= right_val
                if op == ">=": return left_val >= right_val
            else:
                lnum = js_to_number(left_val)
                rnum = js_to_number(right_val)
                if op == "<":  return lnum < rnum
                if op == ">": return lnum > rnum
                if op == "<=": return lnum <= rnum
                if op == ">=": return lnum >= rnum
        
        if op == "in":
            if not isinstance(right_val, JSObject):
                raise TypeError("Cannot use 'in' operator to search in non-object")
            return js_to_string(left_val) in right_val.properties or (isinstance(right_val, JSArray) and js_to_string(left_val).isdigit() and 0 <= int(js_to_string(left_val)) < len(right_val.elements))
            
        raise NotImplementedError(f"Operator {op} not implemented")

    def visit_LogicalExpression(self, node, env):
        left_val = self.evaluate(node.left, env)
        op = node.operator
        
        if op == "&&":
            if not js_to_boolean(left_val):
                return left_val
            return self.evaluate(node.right, env)
            
        if op == "||":
            if js_to_boolean(left_val):
                return left_val
            return self.evaluate(node.right, env)
            
        if op == "??":
            if left_val is not None and left_val is not UNDEFINED:
                return left_val
            return self.evaluate(node.right, env)
            
        raise NotImplementedError(f"Logical operator {op} not implemented")

    def visit_UnaryExpression(self, node, env):
        op = node.operator
        # typeof on undeclared variable should return 'undefined' not throw
        if op == "typeof" and isinstance(node.argument, parser.Identifier):
            try:
                val = self.evaluate(node.argument, env)
            except Exception:
                return "undefined"
            if val is UNDEFINED: return "undefined"
            if val is None: return "object"
            if isinstance(val, bool): return "boolean"
            if isinstance(val, (int, float)): return "number"
            if isinstance(val, str): return "string"
            if isinstance(val, (JSFunction, JSNativeFunction)): return "function"
            if isinstance(val, (JSObject, JSArray)): return "object"
            return "object"
        
        val = self.evaluate(node.argument, env)
        if op == "-": return -js_to_number(val)
        if op == "+": return js_to_number(val)
        if op == "!": return not js_to_boolean(val)
        if op == "typeof":
            if val is UNDEFINED: return "undefined"
            if val is None: return "object"  # JS behavior typeof null === "object"
            if isinstance(val, bool): return "boolean"
            if isinstance(val, (int, float)): return "number"
            if isinstance(val, str): return "string"
            if isinstance(val, (JSFunction, JSNativeFunction)): return "function"
            if isinstance(val, (JSObject, JSArray)): return "object"
            return "object"
        if op == "~":
            return float(~int(js_to_number(val)))
        if op == "void":
            return UNDEFINED
        raise NotImplementedError(f"Unary operator {op} not implemented")

    def visit_UpdateExpression(self, node, env):
        op = node.operator
        
        # Helper to apply increment/decrement
        def update_val(v):
            return v + 1 if op == "++" else v - 1
            
        if isinstance(node.argument, parser.Identifier):
            name = node.argument.name
            old_val = js_to_number(env.get(name))
            new_val = update_val(old_val)
            env.assign(name, new_val)
            return new_val if node.prefix else old_val
            
        if isinstance(node.argument, parser.MemberExpression):
            obj = self.evaluate(node.argument.object, env)
            if obj is None or obj is UNDEFINED:
                raise TypeError("Cannot read properties of undefined")
            
            key = self.evaluate(node.argument.property, env) if node.argument.computed else node.argument.property.name
            
            if isinstance(obj, JSObject):
                old_val = js_to_number(obj.get(key))
                new_val = update_val(old_val)
                obj.set(key, new_val)
                return new_val if node.prefix else old_val
            elif isinstance(obj, str):
                raise TypeError("Cannot assign to read-only property of string")
                
        raise SyntaxError("Invalid left-hand side in assignment")

    def visit_AssignmentExpression(self, node, env):
        op = node.operator
        
        # 1. Evaluate RHS
        rhs_val = self.evaluate(node.right, env)
        
        # 2. Simple Assignment
        if op == "=":
            if isinstance(node.left, parser.Identifier):
                env.assign(node.left.name, rhs_val)
                return rhs_val
            elif isinstance(node.left, parser.MemberExpression):
                obj = self.evaluate(node.left.object, env)
                if obj is None or obj is UNDEFINED:
                    raise TypeError("Cannot set properties of undefined")
                key = self.evaluate(node.left.property, env) if node.left.computed else node.left.property.name
                if isinstance(obj, JSObject):
                    obj.set(key, rhs_val)
                    return rhs_val
                else:
                    raise TypeError(f"Cannot set property {key} on non-object")
            else:
                # Destructuring assignment
                self.assign_pattern(node.left, rhs_val, env)
                return rhs_val
                
        # 3. Compound Assignment (+=, -=, etc.)
        def apply_op(lhs_val):
            if op == "+=":
                if isinstance(lhs_val, str) or isinstance(rhs_val, str):
                    return js_to_string(lhs_val) + js_to_string(rhs_val)
                return js_to_number(lhs_val) + js_to_number(rhs_val)
            if op == "-=": return js_to_number(lhs_val) - js_to_number(rhs_val)
            if op == "*=": return js_to_number(lhs_val) * js_to_number(rhs_val)
            if op == "/=": return js_to_number(lhs_val) / js_to_number(rhs_val)
            if op == "%=": return math.fmod(js_to_number(lhs_val), js_to_number(rhs_val))
            if op == "**=": return js_to_number(lhs_val) ** js_to_number(rhs_val)
            return lhs_val

        if isinstance(node.left, parser.Identifier):
            name = node.left.name
            old_val = env.get(name)
            new_val = apply_op(old_val)
            env.assign(name, new_val)
            return new_val
        elif isinstance(node.left, parser.MemberExpression):
            obj = self.evaluate(node.left.object, env)
            if obj is None or obj is UNDEFINED:
                raise TypeError("Cannot set properties of undefined")
            key = self.evaluate(node.left.property, env) if node.left.computed else node.left.property.name
            if isinstance(obj, JSObject):
                old_val = obj.get(key)
                new_val = apply_op(old_val)
                obj.set(key, new_val)
                return new_val
                
        raise SyntaxError("Invalid left-hand side in assignment")

    def assign_pattern(self, pattern, value, env):
        if isinstance(pattern, parser.Identifier):
            env.assign(pattern.name, value)
        elif isinstance(pattern, parser.ArrayPattern):
            if isinstance(value, JSArray):
                elements = value.elements
            elif isinstance(value, list):
                elements = value
            elif isinstance(value, str):
                elements = list(value)
            else:
                elements = []
                
            for i, subpat in enumerate(pattern.elements):
                if subpat is not None:
                    val = elements[i] if i < len(elements) else UNDEFINED
                    self.assign_pattern(subpat, val, env)
        elif isinstance(pattern, parser.ObjectPattern):
            for prop in pattern.properties:
                if prop.computed:
                    key = self.evaluate(prop.key, env)
                else:
                    key = prop.key.name
                    
                val = UNDEFINED
                if isinstance(value, JSObject):
                    val = value.get(key)
                    
                self.assign_pattern(prop.value, val, env)

    def visit_MemberExpression(self, node, env):
        obj = self.evaluate(node.object, env)
        
        # Optional Chaining check
        if node.optional and (obj is None or obj is UNDEFINED):
            return UNDEFINED
            
        if obj is None or obj is UNDEFINED:
            raise TypeError("Cannot read properties of undefined/null")
            
        key = self.evaluate(node.property, env) if node.computed else node.property.name
        
        if isinstance(obj, JSObject):
            return obj.get(key)
        if isinstance(obj, str):
            return get_string_property(obj, key)
        if isinstance(obj, (int, float)):
            return get_number_property(obj, key)
            
        # For booleans etc., return UNDEFINED
        return UNDEFINED

    def visit_CallExpression(self, node, env):
        # 1. Determine this_arg context
        this_arg = UNDEFINED
        if isinstance(node.callee, parser.MemberExpression):
            # E.g. obj.method() -> 'obj' is this_arg
            obj = self.evaluate(node.callee.object, env)
            
            # Optional chaining check
            if node.callee.optional and (obj is None or obj is UNDEFINED):
                return UNDEFINED
                
            if obj is None or obj is UNDEFINED:
                raise TypeError("Cannot read properties of undefined")
                
            key = self.evaluate(node.callee.property, env) if node.callee.computed else node.callee.property.name
            
            if isinstance(obj, JSObject):
                callee_val = obj.get(key)
            elif isinstance(obj, str):
                callee_val = get_string_property(obj, key)
            else:
                callee_val = UNDEFINED
                
            this_arg = obj
        else:
            callee_val = self.evaluate(node.callee, env)
            
        if node.optional and (callee_val is None or callee_val is UNDEFINED):
            return UNDEFINED
            
        if callee_val is None or callee_val is UNDEFINED:
            raise TypeError(f"'{node.callee}' is not a function")
            
        # 2. Evaluate arguments (with spread support)
        args = []
        for arg in node.arguments:
            if isinstance(arg, parser.SpreadElement):
                spread_val = self.evaluate(arg.argument, env)
                if isinstance(spread_val, JSArray):
                    args.extend(spread_val.elements)
                elif isinstance(spread_val, list):
                    args.extend(spread_val)
                elif isinstance(spread_val, str):
                    args.extend(list(spread_val))
            else:
                args.append(self.evaluate(arg, env))
                
        # 3. Invoke function
        if isinstance(callee_val, (JSFunction, JSNativeFunction)):
            return callee_val.call(self, this_arg, args)
            
        raise TypeError(f"{callee_val} is not a function")

    def visit_ArrayExpression(self, node, env):
        elements = []
        for el in node.elements:
            if isinstance(el, parser.SpreadElement):
                spread_val = self.evaluate(el.argument, env)
                if isinstance(spread_val, JSArray):
                    elements.extend(spread_val.elements)
                elif isinstance(spread_val, list):
                    elements.extend(spread_val)
                elif isinstance(spread_val, str):
                    elements.extend(list(spread_val))
            else:
                elements.append(self.evaluate(el, env))
        return JSArray(elements)

    def visit_ObjectExpression(self, node, env):
        obj = JSObject()
        for prop in node.properties:
            if prop.computed:
                key = self.evaluate(prop.key, env)
            else:
                key = prop.key.value if isinstance(prop.key, parser.Literal) else prop.key.name
                
            val = self.evaluate(prop.value, env)
            obj.set(key, val)
        return obj

    def visit_NewExpression(self, node, env):
        ctor = self.evaluate(node.callee, env)
        
        args = []
        for arg in node.arguments:
            args.append(self.evaluate(arg, env))
            
        if ctor is DATE_CONSTRUCTOR_NATIVE: # check if Date ctor
            return JSDate()
            
        # check constructors
        if isinstance(ctor, JSNativeFunction):
            if ctor.name == "Date":
                return JSDate()
            if ctor.name == "Object":
                return JSObject()
                
        if isinstance(ctor, JSFunction):
            new_obj = JSObject()
            res = ctor.call(self, new_obj, args)
            if isinstance(res, (JSObject, JSArray)):
                return res
            return new_obj
            
        raise TypeError(f"{ctor} is not a constructor")

    def visit_FunctionDeclaration(self, node, env):
        func = JSFunction(node.id.name, node.params, node.body, env, is_arrow=False)
        env.declare(node.id.name, func, is_const=False)
        return UNDEFINED

    def visit_FunctionExpression(self, node, env):
        name = node.id.name if node.id else None
        return JSFunction(name, node.params, node.body, env, is_arrow=False)

    def visit_ArrowFunctionExpression(self, node, env):
        # Wrap expression body in implicit ReturnStatement if not block statement
        body_node = node.body
        if node.expression:
            body_node = parser.BlockStatement([parser.ReturnStatement(node.body)])
        return JSFunction(None, node.params, body_node, env, is_arrow=True)

# Helper constant to match date constructor
DATE_CONSTRUCTOR_NATIVE = JSNativeFunction("Date", lambda interpreter, this, args: JSDate())
