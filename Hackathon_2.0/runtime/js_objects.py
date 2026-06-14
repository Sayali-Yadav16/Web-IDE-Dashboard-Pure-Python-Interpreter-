import math
import functools

class JSUndefined:
    def __repr__(self):
        return "undefined"
    def __str__(self):
        return "undefined"

UNDEFINED = JSUndefined()

def js_to_string(val):
    if val is UNDEFINED:
        return "undefined"
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        if math.isnan(val):
            return "NaN"
        if math.isinf(val):
            return "Infinity" if val > 0 else "-Infinity"
        if isinstance(val, float) and val.is_integer():
            return str(int(val))
        return str(val)
    if isinstance(val, str):
        return val
    if isinstance(val, JSArray):
        return val.join_internal(",")
    if isinstance(val, JSObject):
        return "[object Object]"
    return str(val)

def js_to_boolean(val):
    if val is UNDEFINED or val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        if math.isnan(val):
            return False
        return val != 0
    if isinstance(val, str):
        return val != ""
    return True

def js_to_number(val):
    if val is UNDEFINED:
        return float('nan')
    if val is None:
        return 0.0
    if isinstance(val, bool):
        return 1.0 if val else 0.0
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return 0.0
        try:
            if s.startswith('0x') or s.startswith('0X'):
                return float(int(s, 16))
            return float(s)
        except ValueError:
            return float('nan')
    if isinstance(val, JSArray):
        return js_to_number(js_to_string(val))
    return float('nan')

class JSObject:
    def __init__(self):
        self.properties = {}

    def get(self, key):
        skey = str(key)
        if skey in self.properties:
            return self.properties[skey]
        return UNDEFINED

    def set(self, key, value):
        self.properties[str(key)] = value

    def delete(self, key):
        skey = str(key)
        if skey in self.properties:
            del self.properties[skey]
            return True
        return False

    def __repr__(self):
        return "[object Object]"


class JSFunction(JSObject):
    def __init__(self, name, params, body, env, is_arrow=False):
        super().__init__()
        self.name = name
        self.params = params  # List of param info (name, default, rest)
        self.body = body      # AST node
        self.env = env        # Closure environment
        self.is_arrow = is_arrow

    def call(self, interpreter, this_arg, args):
        from runtime.environment import Environment
        from runtime.interpreter import ReturnException
        
        # Arrow functions inherit 'this' from their defining context lexical scope.
        # Otherwise, use the passed this_arg.
        call_env = Environment(self.env)
        
        # Bind arguments and parameters
        # params is list of dict or objects: (name, is_rest, default_val)
        for i, param in enumerate(self.params):
            param_name = param['name']
            if param.get('is_rest', False):
                rest_args = JSArray(args[i:])
                call_env.declare(param_name, rest_args, is_const=False)
                break
            else:
                val = args[i] if i < len(args) else UNDEFINED
                if val is UNDEFINED and param.get('default') is not None:
                    # evaluate default in call_env or self.env? Standard JS evaluates in call_env
                    val = interpreter.evaluate(param['default'], call_env)
                call_env.declare(param_name, val, is_const=False)

        # Handle 'this'
        if not self.is_arrow:
            call_env.declare("this", this_arg if this_arg is not None else UNDEFINED, is_const=False)

        try:
            interpreter.execute_block(self.body.body, call_env)
        except ReturnException as e:
            return e.value
        return UNDEFINED

    def __repr__(self):
        return f"[Function: {self.name or '(anonymous)'}]"


class JSNativeFunction(JSObject):
    def __init__(self, name, func):
        super().__init__()
        self.name = name
        self.func = func

    def call(self, interpreter, this_arg, args):
        return self.func(interpreter, this_arg, args)

    def __repr__(self):
        return f"[Function: {self.name}]"


class JSArray(JSObject):
    def __init__(self, elements=None):
        super().__init__()
        self.elements = list(elements) if elements is not None else []

    def get(self, key):
        skey = str(key)
        # Check if key is integer index
        if skey.isdigit():
            idx = int(skey)
            if 0 <= idx < len(self.elements):
                return self.elements[idx]
            return UNDEFINED
        
        if skey == "length":
            return float(len(self.elements))
            
        # Return methods
        if skey in ARRAY_METHODS:
            return JSNativeFunction(skey, ARRAY_METHODS[skey])
            
        return super().get(key)

    def set(self, key, value):
        skey = str(key)
        if skey.isdigit():
            idx = int(skey)
            if idx >= len(self.elements):
                # Expand array
                self.elements.extend([UNDEFINED] * (idx - len(self.elements) + 1))
            self.elements[idx] = value
            return
        elif skey == "length":
            try:
                new_len = int(js_to_number(value))
                if new_len < 0 or math.isnan(new_len):
                    raise ValueError("Invalid array length")
                if new_len < len(self.elements):
                    self.elements = self.elements[:new_len]
                elif new_len > len(self.elements):
                    self.elements.extend([UNDEFINED] * (new_len - len(self.elements)))
            except (ValueError, TypeError):
                raise RangeError("Invalid array length")
            return
        super().set(key, value)

    def join_internal(self, separator):
        parts = []
        for el in self.elements:
            if el is UNDEFINED or el is None:
                parts.append("")
            else:
                parts.append(js_to_string(el))
        return separator.join(parts)

    def __repr__(self):
        return f"[{', '.join(js_to_string(x) for x in self.elements)}]"

# Implement Array methods
def array_push(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    for arg in args:
        this_arg.elements.append(arg)
    return float(len(this_arg.elements))

def array_pop(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    if not this_arg.elements:
        return UNDEFINED
    return this_arg.elements.pop()

def array_shift(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    if not this_arg.elements:
        return UNDEFINED
    return this_arg.elements.pop(0)

def array_unshift(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    for arg in reversed(args):
        this_arg.elements.insert(0, arg)
    return float(len(this_arg.elements))

def array_slice(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    length = len(this_arg.elements)
    start = 0
    end = length
    if len(args) > 0:
        start = int(js_to_number(args[0]))
        if start < 0:
            start = max(length + start, 0)
        else:
            start = min(start, length)
    if len(args) > 1:
        end = int(js_to_number(args[1]))
        if end < 0:
            end = max(length + end, 0)
        else:
            end = min(end, length)
    
    return JSArray(this_arg.elements[start:end])

def array_splice(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    length = len(this_arg.elements)
    if not args:
        return JSArray()
    
    start = int(js_to_number(args[0]))
    if start < 0:
        start = max(length + start, 0)
    else:
        start = min(start, length)
        
    delete_count = length - start
    if len(args) > 1:
        delete_count = int(js_to_number(args[1]))
        delete_count = max(0, min(delete_count, length - start))
        
    insert_items = args[2:]
    
    deleted = this_arg.elements[start : start + delete_count]
    this_arg.elements[start : start + delete_count] = insert_items
    return JSArray(deleted)

def array_concat(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    new_elements = list(this_arg.elements)
    for arg in args:
        if isinstance(arg, JSArray):
            new_elements.extend(arg.elements)
        else:
            new_elements.append(arg)
    return JSArray(new_elements)

def array_includes(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    if not args:
        return False
    search_element = args[0]
    from_index = 0
    if len(args) > 1:
        from_index = int(js_to_number(args[1]))
        if from_index < 0:
            from_index = max(len(this_arg.elements) + from_index, 0)
            
    for i in range(from_index, len(this_arg.elements)):
        # === check
        if interpreter_strict_equals(this_arg.elements[i], search_element):
            return True
    return False

def array_indexOf(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    if not args:
        return -1.0
    search_element = args[0]
    from_index = 0
    if len(args) > 1:
        from_index = int(js_to_number(args[1]))
        if from_index < 0:
            from_index = max(len(this_arg.elements) + from_index, 0)
            
    for i in range(from_index, len(this_arg.elements)):
        if interpreter_strict_equals(this_arg.elements[i], search_element):
            return float(i)
    return -1.0

def array_sort(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    
    compare_fn = args[0] if args else None
    
    if compare_fn is not None and isinstance(compare_fn, (JSFunction, JSNativeFunction)):
        # Custom comparator
        def cmp_wrapper(a, b):
            res = compare_fn.call(interpreter, UNDEFINED, [a, b])
            n = js_to_number(res)
            if n < 0:
                return -1
            elif n > 0:
                return 1
            return 0
        this_arg.elements.sort(key=functools.cmp_to_key(cmp_wrapper))
    else:
        # Default string sort (JS spec: convert to string then lexicographic)
        this_arg.elements.sort(key=lambda x: js_to_string(x))
        
    return this_arg

def array_reverse(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    this_arg.elements.reverse()
    return this_arg

def array_join(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    separator = js_to_string(args[0]) if args else ","
    return this_arg.join_internal(separator)

def array_map(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    if not args:
        raise TypeError("Undefined is not a function")
    callback = args[0]
    cb_this = args[1] if len(args) > 1 else UNDEFINED
    
    mapped = []
    for i, el in enumerate(this_arg.elements):
        res = callback.call(interpreter, cb_this, [el, float(i), this_arg])
        mapped.append(res)
    return JSArray(mapped)

def array_filter(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    if not args:
        raise TypeError("Undefined is not a function")
    callback = args[0]
    cb_this = args[1] if len(args) > 1 else UNDEFINED
    
    filtered = []
    for i, el in enumerate(this_arg.elements):
        res = callback.call(interpreter, cb_this, [el, float(i), this_arg])
        if js_to_boolean(res):
            filtered.append(el)
    return JSArray(filtered)

def array_reduce(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    if not args:
        raise TypeError("Undefined is not a function")
    callback = args[0]
    
    has_initial = len(args) > 1
    if not this_arg.elements and not has_initial:
        raise TypeError("Reduce of empty array with no initial value")
        
    start_idx = 0
    if has_initial:
        accumulator = args[1]
    else:
        accumulator = this_arg.elements[0]
        start_idx = 1
        
    for i in range(start_idx, len(this_arg.elements)):
        accumulator = callback.call(interpreter, UNDEFINED, [accumulator, this_arg.elements[i], float(i), this_arg])
        
    return accumulator

def array_find(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    if not args:
        raise TypeError("Undefined is not a function")
    callback = args[0]
    cb_this = args[1] if len(args) > 1 else UNDEFINED
    
    for i, el in enumerate(this_arg.elements):
        res = callback.call(interpreter, cb_this, [el, float(i), this_arg])
        if js_to_boolean(res):
            return el
    return UNDEFINED

def array_findIndex(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    if not args:
        raise TypeError("Undefined is not a function")
    callback = args[0]
    cb_this = args[1] if len(args) > 1 else UNDEFINED
    
    for i, el in enumerate(this_arg.elements):
        res = callback.call(interpreter, cb_this, [el, float(i), this_arg])
        if js_to_boolean(res):
            return float(i)
    return -1.0

def array_some(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    if not args:
        raise TypeError("Undefined is not a function")
    callback = args[0]
    cb_this = args[1] if len(args) > 1 else UNDEFINED
    
    for i, el in enumerate(this_arg.elements):
        res = callback.call(interpreter, cb_this, [el, float(i), this_arg])
        if js_to_boolean(res):
            return True
    return False

def array_every(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    if not args:
        raise TypeError("Undefined is not a function")
    callback = args[0]
    cb_this = args[1] if len(args) > 1 else UNDEFINED
    
    for i, el in enumerate(this_arg.elements):
        res = callback.call(interpreter, cb_this, [el, float(i), this_arg])
        if not js_to_boolean(res):
            return False
    return True

def array_forEach(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    if not args:
        raise TypeError("Undefined is not a function")
    callback = args[0]
    cb_this = args[1] if len(args) > 1 else UNDEFINED
    
    for i, el in enumerate(this_arg.elements):
        callback.call(interpreter, cb_this, [el, float(i), this_arg])
    return UNDEFINED

def array_flat(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    depth = int(js_to_number(args[0])) if args else 1
    
    def flatten(arr, d):
        if d <= 0:
            return list(arr.elements)
        flat_list = []
        for item in arr.elements:
            if isinstance(item, JSArray):
                flat_list.extend(flatten(item, d - 1))
            else:
                flat_list.append(item)
        return flat_list
        
    return JSArray(flatten(this_arg, depth))

def array_fill(interpreter, this_arg, args):
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    if not args:
        return this_arg
    val = args[0]
    length = len(this_arg.elements)
    
    start = 0
    if len(args) > 1:
        start = int(js_to_number(args[1]))
        if start < 0:
            start = max(length + start, 0)
        else:
            start = min(start, length)
            
    end = length
    if len(args) > 2:
        end = int(js_to_number(args[2]))
        if end < 0:
            end = max(length + end, 0)
        else:
            end = min(end, length)
            
    for i in range(start, end):
        this_arg.elements[i] = val
    return this_arg


def array_flatMap(interpreter, this_arg, args):
    """Array.prototype.flatMap — map then flat(1)"""
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    if not args:
        raise TypeError("Undefined is not a function")
    callback = args[0]
    cb_this = args[1] if len(args) > 1 else UNDEFINED
    
    result = []
    for i, el in enumerate(this_arg.elements):
        res = callback.call(interpreter, cb_this, [el, float(i), this_arg])
        if isinstance(res, JSArray):
            result.extend(res.elements)
        else:
            result.append(res)
    return JSArray(result)


def array_reduceRight(interpreter, this_arg, args):
    """Array.prototype.reduceRight — reduce from right to left"""
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    if not args:
        raise TypeError("Undefined is not a function")
    callback = args[0]
    
    has_initial = len(args) > 1
    elems = this_arg.elements
    if not elems and not has_initial:
        raise TypeError("Reduce of empty array with no initial value")
        
    if has_initial:
        accumulator = args[1]
        start_idx = len(elems) - 1
    else:
        accumulator = elems[-1]
        start_idx = len(elems) - 2
        
    for i in range(start_idx, -1, -1):
        accumulator = callback.call(interpreter, UNDEFINED, [accumulator, elems[i], float(i), this_arg])
        
    return accumulator


def array_at(interpreter, this_arg, args):
    """Array.prototype.at — supports negative indices"""
    if not isinstance(this_arg, JSArray):
        raise TypeError("Method called on incompatible receiver")
    if not args:
        return UNDEFINED
    idx = int(js_to_number(args[0]))
    length = len(this_arg.elements)
    if idx < 0:
        idx = length + idx
    if 0 <= idx < length:
        return this_arg.elements[idx]
    return UNDEFINED


def array_from_static(interpreter, this_arg, args):
    """Array.from static method — converts iterable/array-like to JSArray"""
    if not args:
        return JSArray()
    source = args[0]
    map_fn = args[1] if len(args) > 1 else None
    
    if isinstance(source, JSArray):
        elements = list(source.elements)
    elif isinstance(source, str):
        elements = list(source)
    elif isinstance(source, JSObject) and not isinstance(source, JSArray):
        # array-like with length
        length_val = source.get("length")
        if length_val is UNDEFINED:
            elements = []
        else:
            n = int(js_to_number(length_val))
            elements = [source.get(str(i)) for i in range(n)]
    else:
        elements = []
    
    if map_fn is not None and isinstance(map_fn, (JSFunction, JSNativeFunction)):
        mapped = []
        for i, el in enumerate(elements):
            mapped.append(map_fn.call(interpreter, UNDEFINED, [el, float(i)]))
        elements = mapped
    
    return JSArray(elements)


ARRAY_METHODS = {
    "push": array_push,
    "pop": array_pop,
    "shift": array_shift,
    "unshift": array_unshift,
    "slice": array_slice,
    "splice": array_splice,
    "concat": array_concat,
    "includes": array_includes,
    "indexOf": array_indexOf,
    "sort": array_sort,
    "reverse": array_reverse,
    "join": array_join,
    "map": array_map,
    "filter": array_filter,
    "reduce": array_reduce,
    "reduceRight": array_reduceRight,
    "find": array_find,
    "findIndex": array_findIndex,
    "some": array_some,
    "every": array_every,
    "forEach": array_forEach,
    "flat": array_flat,
    "flatMap": array_flatMap,
    "fill": array_fill,
    "at": array_at,
}



def interpreter_strict_equals(a, b):
    # Helper to prevent circular dependency, handles JS === comparison
    if type(a) != type(b):
        return False
    if a is UNDEFINED and b is UNDEFINED:
        return True
    if a is None and b is None:
        return True
    if isinstance(a, (int, float)):
        if math.isnan(a) or math.isnan(b):
            return False
        return float(a) == float(b)
    if isinstance(a, (JSArray, JSObject, JSFunction, JSNativeFunction)):
        return a is b
    return a == b
