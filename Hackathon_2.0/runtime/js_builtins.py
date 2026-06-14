import math
import random
import datetime
import json
from runtime.js_objects import (
    JSObject, JSArray, JSNativeFunction, JSFunction, UNDEFINED,
    js_to_string, js_to_number, js_to_boolean, interpreter_strict_equals
)

# ----------------- JSDate Class -----------------
class JSDate(JSObject):
    def __init__(self, dt=None):
        super().__init__()
        self.dt = dt or datetime.datetime.now()

    def get(self, key):
        skey = str(key)
        if skey in DATE_METHODS:
            return JSNativeFunction(skey, DATE_METHODS[skey])
        return super().get(key)

    def __repr__(self):
        return self.dt.isoformat() + "Z"

def date_getFullYear(interpreter, this_arg, args):
    if not isinstance(this_arg, JSDate):
        raise TypeError("Method called on incompatible receiver")
    return float(this_arg.dt.year)

def date_getMonth(interpreter, this_arg, args):
    if not isinstance(this_arg, JSDate):
        raise TypeError("Method called on incompatible receiver")
    # JS months are 0-indexed
    return float(this_arg.dt.month - 1)

def date_getDate(interpreter, this_arg, args):
    if not isinstance(this_arg, JSDate):
        raise TypeError("Method called on incompatible receiver")
    return float(this_arg.dt.day)

def date_getHours(interpreter, this_arg, args):
    if not isinstance(this_arg, JSDate):
        raise TypeError("Method called on incompatible receiver")
    return float(this_arg.dt.hour)

def date_getMinutes(interpreter, this_arg, args):
    if not isinstance(this_arg, JSDate):
        raise TypeError("Method called on incompatible receiver")
    return float(this_arg.dt.minute)

def date_getSeconds(interpreter, this_arg, args):
    if not isinstance(this_arg, JSDate):
        raise TypeError("Method called on incompatible receiver")
    return float(this_arg.dt.second)

def date_toLocaleDateString(interpreter, this_arg, args):
    if not isinstance(this_arg, JSDate):
        raise TypeError("Method called on incompatible receiver")
    return this_arg.dt.strftime("%Y-%m-%d")

def date_toLocaleString(interpreter, this_arg, args):
    if not isinstance(this_arg, JSDate):
        raise TypeError("Method called on incompatible receiver")
    return this_arg.dt.strftime("%Y-%m-%d %H:%M:%S")

def date_toISOString(interpreter, this_arg, args):
    if not isinstance(this_arg, JSDate):
        raise TypeError("Method called on incompatible receiver")
    return this_arg.dt.isoformat() + "Z"

DATE_METHODS = {
    "getFullYear": date_getFullYear,
    "getMonth": date_getMonth,
    "getDate": date_getDate,
    "getHours": date_getHours,
    "getMinutes": date_getMinutes,
    "getSeconds": date_getSeconds,
    "toLocaleDateString": date_toLocaleDateString,
    "toLocaleString": date_toLocaleString,
    "toISOString": date_toISOString
}

def date_constructor(interpreter, this_arg, args):
    # Returns a new Date
    return JSDate()

# ----------------- Number property interceptor -----------------
def get_number_property(num_val, key):
    skey = str(key)
    if skey == "toFixed":
        def to_fixed(interpreter, this, args):
            digits = int(js_to_number(args[0])) if args else 0
            return f"{float(num_val):.{digits}f}"
        return JSNativeFunction("toFixed", to_fixed)
    if skey == "toString":
        def to_string_num(interpreter, this, args):
            radix = int(js_to_number(args[0])) if args else 10
            n = num_val
            if radix == 10:
                return js_to_string(n)
            # Integer representation in different bases
            n_int = int(n)
            return format(n_int, f'0{chr(ord("a") + radix - 10 - 1 + 10)}') if radix > 10 else format(n_int, 'b' if radix == 2 else 'o' if radix == 8 else 'd')
        return JSNativeFunction("toString", to_string_num)
    if skey == "toPrecision":
        def to_precision(interpreter, this, args):
            if not args or args[0] is UNDEFINED:
                return js_to_string(num_val)
            p = int(js_to_number(args[0]))
            return f"{float(num_val):.{p}g}"
        return JSNativeFunction("toPrecision", to_precision)
    return UNDEFINED

# ----------------- String methods interceptor -----------------
def get_string_property(str_val, key):
    skey = str(key)
    if skey == "length":
        return float(len(str_val))
    if skey.isdigit():
        idx = int(skey)
        if 0 <= idx < len(str_val):
            return str_val[idx]
        return UNDEFINED
    if skey in STRING_METHODS:
        return JSNativeFunction(skey, STRING_METHODS[skey])
    return UNDEFINED

# Implement String methods
def string_split(interpreter, this_arg, args):
    s = js_to_string(this_arg)
    sep = js_to_string(args[0]) if args else None
    
    if sep is None:
        return JSArray([s])
    if sep == "":
        return JSArray(list(s))
    
    parts = s.split(sep)
    return JSArray(parts)

def string_replace(interpreter, this_arg, args):
    s = js_to_string(this_arg)
    if len(args) < 2:
        return s
    search = js_to_string(args[0])
    replace = js_to_string(args[1])
    return s.replace(search, replace, 1)

def string_replaceAll(interpreter, this_arg, args):
    s = js_to_string(this_arg)
    if len(args) < 2:
        return s
    search = js_to_string(args[0])
    replace = js_to_string(args[1])
    return s.replace(search, replace)

def string_substring(interpreter, this_arg, args):
    s = js_to_string(this_arg)
    length = len(s)
    start = 0
    end = length
    if len(args) > 0:
        start = max(0, min(int(js_to_number(args[0])), length))
    if len(args) > 1:
        end = max(0, min(int(js_to_number(args[1])), length))
    if start > end:
        start, end = end, start
    return s[start:end]

def string_slice(interpreter, this_arg, args):
    s = js_to_string(this_arg)
    length = len(s)
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
    return s[start:end]

def string_trim(interpreter, this_arg, args):
    return js_to_string(this_arg).strip()

def string_trimStart(interpreter, this_arg, args):
    return js_to_string(this_arg).lstrip()

def string_trimEnd(interpreter, this_arg, args):
    return js_to_string(this_arg).rstrip()

def string_toUpperCase(interpreter, this_arg, args):
    return js_to_string(this_arg).upper()

def string_toLowerCase(interpreter, this_arg, args):
    return js_to_string(this_arg).lower()

def string_includes(interpreter, this_arg, args):
    s = js_to_string(this_arg)
    search = js_to_string(args[0]) if args else "undefined"
    return search in s

def string_startsWith(interpreter, this_arg, args):
    s = js_to_string(this_arg)
    search = js_to_string(args[0]) if args else "undefined"
    return s.startswith(search)

def string_endsWith(interpreter, this_arg, args):
    s = js_to_string(this_arg)
    search = js_to_string(args[0]) if args else "undefined"
    return s.endswith(search)

def string_indexOf(interpreter, this_arg, args):
    s = js_to_string(this_arg)
    search = js_to_string(args[0]) if args else "undefined"
    from_index = 0
    if len(args) > 1:
        from_index = max(0, int(js_to_number(args[1])))
    return float(s.find(search, from_index))

def string_lastIndexOf(interpreter, this_arg, args):
    s = js_to_string(this_arg)
    search = js_to_string(args[0]) if args else "undefined"
    # Python rfind returns -1 if not found, same as JS
    return float(s.rfind(search))

def string_padStart(interpreter, this_arg, args):
    s = js_to_string(this_arg)
    if not args:
        return s
    target_len = int(js_to_number(args[0]))
    pad_str = js_to_string(args[1]) if len(args) > 1 else " "
    if len(s) >= target_len:
        return s
    needed = target_len - len(s)
    # Repeat pad_str until it matches needed length
    repeated = (pad_str * (needed // len(pad_str) + 1))[:needed]
    return repeated + s

def string_padEnd(interpreter, this_arg, args):
    s = js_to_string(this_arg)
    if not args:
        return s
    target_len = int(js_to_number(args[0]))
    pad_str = js_to_string(args[1]) if len(args) > 1 else " "
    if len(s) >= target_len:
        return s
    needed = target_len - len(s)
    repeated = (pad_str * (needed // len(pad_str) + 1))[:needed]
    return s + repeated

def string_repeat(interpreter, this_arg, args):
    s = js_to_string(this_arg)
    count = int(js_to_number(args[0])) if args else 0
    if count < 0:
        raise RangeError("Invalid count value")
    return s * count

def string_charAt(interpreter, this_arg, args):
    s = js_to_string(this_arg)
    idx = int(js_to_number(args[0])) if args else 0
    if 0 <= idx < len(s):
        return s[idx]
    return ""

def string_charCodeAt(interpreter, this_arg, args):
    s = js_to_string(this_arg)
    idx = int(js_to_number(args[0])) if args else 0
    if 0 <= idx < len(s):
        return float(ord(s[idx]))
    return float('nan')

STRING_METHODS = {
    "split": string_split,
    "replace": string_replace,
    "replaceAll": string_replaceAll,
    "substring": string_substring,
    "slice": string_slice,
    "trim": string_trim,
    "trimStart": string_trimStart,
    "trimEnd": string_trimEnd,
    "toUpperCase": string_toUpperCase,
    "toLowerCase": string_toLowerCase,
    "includes": string_includes,
    "startsWith": string_startsWith,
    "endsWith": string_endsWith,
    "indexOf": string_indexOf,
    "lastIndexOf": string_lastIndexOf,
    "padStart": string_padStart,
    "padEnd": string_padEnd,
    "repeat": string_repeat,
    "charAt": string_charAt,
    "charCodeAt": string_charCodeAt
}


# ----------------- Global Functions -----------------
def global_parse_int(interpreter, this_arg, args):
    if not args:
        return float('nan')
    s = js_to_string(args[0]).strip()
    # Find first prefix matching integer pattern
    # Optional sign, followed by digits
    # JS parseInt also supports radix, but let's parse standard decimal
    radix = 10
    if len(args) > 1:
        r = int(js_to_number(args[1]))
        if 2 <= r <= 36:
            radix = r
            
    # Simple prefix parser
    sign = 1
    if s.startswith('-'):
        sign = -1
        s = s[1:]
    elif s.startswith('+'):
        s = s[1:]
        
    if radix == 16 and (s.startswith('0x') or s.startswith('0X')):
        s = s[2:]
        
    chars = []
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    allowed = digits[:radix]
    for char in s.lower():
        if char in allowed:
            chars.append(char)
        else:
            break
            
    if not chars:
        return float('nan')
    try:
        return float(sign * int("".join(chars), radix))
    except ValueError:
        return float('nan')

def global_parse_float(interpreter, this_arg, args):
    if not args:
        return float('nan')
    s = js_to_string(args[0]).strip()
    # Find prefix that looks like float
    sign = ""
    if s.startswith('-'):
        sign = "-"
        s = s[1:]
    elif s.startswith('+'):
        s = s[1:]
        
    chars = []
    has_dot = False
    has_e = False
    for i, char in enumerate(s):
        if char.isdigit():
            chars.append(char)
        elif char == '.' and not has_dot and not has_e:
            has_dot = True
            chars.append(char)
        elif char in ('e', 'E') and not has_e and chars:
            has_e = True
            chars.append(char)
            # handle optional sign after e
            if i + 1 < len(s) and s[i+1] in ('+', '-'):
                chars.append(s[i+1])
        else:
            break
            
    if not chars:
        return float('nan')
    try:
        return float(sign + "".join(chars))
    except ValueError:
        return float('nan')

def global_is_nan(interpreter, this_arg, args):
    val = js_to_number(args[0]) if args else float('nan')
    return math.isnan(val)

def global_is_finite(interpreter, this_arg, args):
    if not args:
        return False
    val = js_to_number(args[0])
    return not math.isnan(val) and not math.isinf(val)

def global_set_timeout(interpreter, this_arg, args):
    if not args:
        return UNDEFINED
    callback = args[0]
    cb_args = args[2:] if len(args) > 2 else []
    # execute immediately
    if isinstance(callback, (JSFunction, JSNativeFunction)):
        callback.call(interpreter, UNDEFINED, cb_args)
    return UNDEFINED

def global_string_constructor(interpreter, this_arg, args):
    if not args:
        return ""
    return js_to_string(args[0])

def global_number_constructor(interpreter, this_arg, args):
    if not args:
        return 0.0
    return js_to_number(args[0])

def global_boolean_constructor(interpreter, this_arg, args):
    if not args:
        return False
    return js_to_boolean(args[0])


# ----------------- Math Object -----------------
def create_math_object():
    obj = JSObject()
    obj.set("PI", math.pi)
    obj.set("E", math.e)
    obj.set("LN2", math.log(2))
    obj.set("LN10", math.log(10))
    obj.set("LOG2E", math.log2(math.e))
    obj.set("LOG10E", math.log10(math.e))
    obj.set("SQRT2", math.sqrt(2))
    
    obj.set("floor", JSNativeFunction("floor", lambda interpreter, this, args: float(math.floor(js_to_number(args[0]))) if args else float('nan')))
    obj.set("ceil", JSNativeFunction("ceil", lambda interpreter, this, args: float(math.ceil(js_to_number(args[0]))) if args else float('nan')))
    obj.set("round", JSNativeFunction("round", lambda interpreter, this, args: float(math.floor(js_to_number(args[0]) + 0.5)) if args else float('nan')))
    obj.set("abs", JSNativeFunction("abs", lambda interpreter, this, args: float(abs(js_to_number(args[0]))) if args else float('nan')))
    obj.set("sqrt", JSNativeFunction("sqrt", lambda interpreter, this, args: float(math.sqrt(js_to_number(args[0]))) if args and js_to_number(args[0]) >= 0 else float('nan')))
    obj.set("cbrt", JSNativeFunction("cbrt", lambda interpreter, this, args: float(math.copysign(abs(js_to_number(args[0])) ** (1/3), js_to_number(args[0]))) if args else float('nan')))
    obj.set("pow", JSNativeFunction("pow", lambda interpreter, this, args: float(js_to_number(args[0]) ** js_to_number(args[1])) if len(args) >= 2 else float('nan')))
    obj.set("sin", JSNativeFunction("sin", lambda interpreter, this, args: float(math.sin(js_to_number(args[0]))) if args else float('nan')))
    obj.set("cos", JSNativeFunction("cos", lambda interpreter, this, args: float(math.cos(js_to_number(args[0]))) if args else float('nan')))
    obj.set("tan", JSNativeFunction("tan", lambda interpreter, this, args: float(math.tan(js_to_number(args[0]))) if args else float('nan')))
    obj.set("asin", JSNativeFunction("asin", lambda interpreter, this, args: float(math.asin(js_to_number(args[0]))) if args else float('nan')))
    obj.set("acos", JSNativeFunction("acos", lambda interpreter, this, args: float(math.acos(js_to_number(args[0]))) if args else float('nan')))
    obj.set("atan", JSNativeFunction("atan", lambda interpreter, this, args: float(math.atan(js_to_number(args[0]))) if args else float('nan')))
    
    def math_atan2(interpreter, this, args):
        if len(args) < 2:
            return float('nan')
        return float(math.atan2(js_to_number(args[0]), js_to_number(args[1])))
    obj.set("atan2", JSNativeFunction("atan2", math_atan2))
    
    def math_hypot(interpreter, this, args):
        if not args:
            return 0.0
        return float(math.hypot(*(js_to_number(a) for a in args)))
    obj.set("hypot", JSNativeFunction("hypot", math_hypot))
    
    def math_max(interpreter, this, args):
        if not args:
            return -float('inf')
        try:
            vals = [js_to_number(x) for x in args]
            if any(math.isnan(v) for v in vals):
                return float('nan')
            return float(max(vals))
        except ValueError:
            return float('nan')
    obj.set("max", JSNativeFunction("max", math_max))
    
    def math_min(interpreter, this, args):
        if not args:
            return float('inf')
        try:
            vals = [js_to_number(x) for x in args]
            if any(math.isnan(v) for v in vals):
                return float('nan')
            return float(min(vals))
        except ValueError:
            return float('nan')
    obj.set("min", JSNativeFunction("min", math_min))
    
    def math_log(interpreter, this, args):
        if not args:
            return float('nan')
        val = js_to_number(args[0])
        if val < 0:
            return float('nan')
        if val == 0:
            return -float('inf')
        return float(math.log(val))
    obj.set("log", JSNativeFunction("log", math_log))
    
    def math_log2(interpreter, this, args):
        if not args:
            return float('nan')
        val = js_to_number(args[0])
        if val < 0:
            return float('nan')
        if val == 0:
            return -float('inf')
        return float(math.log2(val))
    obj.set("log2", JSNativeFunction("log2", math_log2))
    
    def math_log10(interpreter, this, args):
        if not args:
            return float('nan')
        val = js_to_number(args[0])
        if val < 0:
            return float('nan')
        if val == 0:
            return -float('inf')
        return float(math.log10(val))
    obj.set("log10", JSNativeFunction("log10", math_log10))
    
    obj.set("random", JSNativeFunction("random", lambda interpreter, this, args: random.random()))
    obj.set("trunc", JSNativeFunction("trunc", lambda interpreter, this, args: float(math.trunc(js_to_number(args[0]))) if args else float('nan')))
    
    def math_sign(interpreter, this, args):
        if not args:
            return float('nan')
        val = js_to_number(args[0])
        if math.isnan(val) or val == 0:
            return val
        return 1.0 if val > 0 else -1.0
    obj.set("sign", JSNativeFunction("sign", math_sign))
    
    def math_clz32(interpreter, this, args):
        if not args:
            return 32.0
        val = int(js_to_number(args[0])) & 0xFFFFFFFF
        if val == 0:
            return 32.0
        return float(32 - val.bit_length())
    obj.set("clz32", JSNativeFunction("clz32", math_clz32))
    
    def math_fround(interpreter, this, args):
        if not args:
            return float('nan')
        import struct
        val = js_to_number(args[0])
        return float(struct.unpack('f', struct.pack('f', val))[0])
    obj.set("fround", JSNativeFunction("fround", math_fround))
    
    return obj



# ----------------- JSON Object -----------------
def create_json_object():
    obj = JSObject()
    
    def stringify_wrapper(interpreter, this, args):
        if not args:
            return UNDEFINED
        return json_stringify(args[0])
        
    def parse_wrapper(interpreter, this, args):
        if not args:
            raise TypeError("JSON.parse: unexpected end of data")
        return json_parse(js_to_string(args[0]))
        
    obj.set("stringify", JSNativeFunction("stringify", stringify_wrapper))
    obj.set("parse", JSNativeFunction("parse", parse_wrapper))
    return obj

def json_stringify(val):
    if val is UNDEFINED:
        return None
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        if math.isnan(val) or math.isinf(val):
            return "null"
        if isinstance(val, float) and val.is_integer():
            return str(int(val))
        return str(val)
    if isinstance(val, str):
        # standard JSON escape
        return json.dumps(val)
    if isinstance(val, JSArray):
        parts = []
        for x in val.elements:
            res = json_stringify(x)
            parts.append(res if res is not None else "null")
        return "[" + ",".join(parts) + "]"
    if isinstance(val, JSObject):
        parts = []
        for k, v in val.properties.items():
            if v is UNDEFINED or isinstance(v, (JSFunction, JSNativeFunction)):
                continue
            res = json_stringify(v)
            if res is not None:
                parts.append(f'"{k}":{res}')
        return "{" + ",".join(parts) + "}"
    return "null"

def json_parse(s):
    try:
        py_val = json.loads(s)
    except Exception:
        raise SyntaxError("Unexpected token in JSON")
        
    def convert(val):
        if isinstance(val, list):
            return JSArray([convert(x) for x in val])
        if isinstance(val, dict):
            obj = JSObject()
            for k, v in val.items():
                obj.set(k, convert(v))
            return obj
        if isinstance(val, (int, float)):
            return float(val)
        return val
        
    return convert(py_val)


# ----------------- console Object -----------------
def create_console_object():
    obj = JSObject()
    
    def log_wrapper(interpreter, this, args):
        msg = " ".join(js_to_string(x) for x in args)
        interpreter.stdout_buffer.append(msg)
        return UNDEFINED
        
    def error_wrapper(interpreter, this, args):
        msg = " ".join(js_to_string(x) for x in args)
        interpreter.stdout_buffer.append(f"[ERROR] {msg}")
        return UNDEFINED
        
    def warn_wrapper(interpreter, this, args):
        msg = " ".join(js_to_string(x) for x in args)
        interpreter.stdout_buffer.append(f"[WARN] {msg}")
        return UNDEFINED
        
    obj.set("log", JSNativeFunction("log", log_wrapper))
    obj.set("error", JSNativeFunction("error", error_wrapper))
    obj.set("warn", JSNativeFunction("warn", warn_wrapper))
    return obj


# ----------------- Object Constructor Object -----------------
def create_object_constructor():
    obj = JSNativeFunction("Object", lambda interpreter, this, args: JSObject())
    
    def keys_fn(interpreter, this, args):
        if not args or args[0] is UNDEFINED or args[0] is None:
            raise TypeError("Cannot convert undefined or null to object")
        target = args[0]
        if isinstance(target, JSArray):
            return JSArray([str(i) for i in range(len(target.elements))])
        if isinstance(target, JSObject):
            return JSArray(list(target.properties.keys()))
        return JSArray()
        
    def values_fn(interpreter, this, args):
        if not args or args[0] is UNDEFINED or args[0] is None:
            raise TypeError("Cannot convert undefined or null to object")
        target = args[0]
        if isinstance(target, JSArray):
            return JSArray(list(target.elements))
        if isinstance(target, JSObject):
            return JSArray(list(target.properties.values()))
        return JSArray()
        
    def entries_fn(interpreter, this, args):
        if not args or args[0] is UNDEFINED or args[0] is None:
            raise TypeError("Cannot convert undefined or null to object")
        target = args[0]
        if isinstance(target, JSArray):
            entries = [JSArray([str(i), target.elements[i]]) for i in range(len(target.elements))]
            return JSArray(entries)
        if isinstance(target, JSObject):
            entries = [JSArray([k, v]) for k, v in target.properties.items()]
            return JSArray(entries)
        return JSArray()
    
    def assign_fn(interpreter, this, args):
        """Object.assign(target, ...sources)"""
        if not args or args[0] is UNDEFINED or args[0] is None:
            raise TypeError("Cannot convert undefined or null to object")
        target = args[0]
        if not isinstance(target, JSObject):
            return target
        for source in args[1:]:
            if source is UNDEFINED or source is None:
                continue
            if isinstance(source, JSObject):
                for k, v in source.properties.items():
                    target.set(k, v)
        return target
        
    def from_entries_fn(interpreter, this, args):
        """Object.fromEntries(iterable)"""
        if not args:
            raise TypeError("Object.fromEntries: argument must be iterable")
        source = args[0]
        result = JSObject()
        if isinstance(source, JSArray):
            for item in source.elements:
                if isinstance(item, JSArray) and len(item.elements) >= 2:
                    key = js_to_string(item.elements[0])
                    result.set(key, item.elements[1])
        return result
        
    obj.set("keys", JSNativeFunction("keys", keys_fn))
    obj.set("values", JSNativeFunction("values", values_fn))
    obj.set("entries", JSNativeFunction("entries", entries_fn))
    obj.set("assign", JSNativeFunction("assign", assign_fn))
    obj.set("fromEntries", JSNativeFunction("fromEntries", from_entries_fn))
    return obj


# ----------------- Array Constructor Object -----------------
def create_array_constructor():
    from runtime.js_objects import array_from_static
    obj = JSNativeFunction("Array", lambda interpreter, this, args: JSArray(args) if args else JSArray())
    obj.set("from", JSNativeFunction("from", array_from_static))
    
    def array_isarray(interpreter, this, args):
        if not args:
            return False
        return isinstance(args[0], JSArray)
    obj.set("isArray", JSNativeFunction("isArray", array_isarray))
    
    def array_of(interpreter, this, args):
        return JSArray(list(args))
    obj.set("of", JSNativeFunction("of", array_of))
    
    return obj


# ----------------- Number Constructor Object -----------------
def create_number_constructor():
    obj = JSNativeFunction("Number", global_number_constructor)
    obj.set("isNaN", JSNativeFunction("isNaN",
        lambda interpreter, this, args: isinstance(args[0], float) and math.isnan(args[0]) if args else False))
    obj.set("isFinite", JSNativeFunction("isFinite",
        lambda interpreter, this, args: isinstance(args[0], (int, float)) and not math.isnan(args[0]) and not math.isinf(args[0]) if args else False))
    obj.set("isInteger", JSNativeFunction("isInteger",
        lambda interpreter, this, args: isinstance(args[0], float) and args[0].is_integer() if args else False))
    obj.set("parseInt", JSNativeFunction("parseInt", global_parse_int))
    obj.set("parseFloat", JSNativeFunction("parseFloat", global_parse_float))
    obj.set("MAX_SAFE_INTEGER", float(2**53 - 1))
    obj.set("MIN_SAFE_INTEGER", float(-(2**53 - 1)))
    obj.set("POSITIVE_INFINITY", float('inf'))
    obj.set("NEGATIVE_INFINITY", -float('inf'))
    obj.set("NaN", float('nan'))
    obj.set("EPSILON", 2.220446049250313e-16)
    
    def to_fixed_fn(interpreter, this, args):
        """Number.prototype.toFixed — called as method on a number"""
        digits = int(js_to_number(args[0])) if args else 0
        return f"{js_to_number(this):.{digits}f}"
    obj.set("toFixed", JSNativeFunction("toFixed", to_fixed_fn))
    return obj


# ----------------- Setup Global Environment -----------------
def setup_global_environment(env):
    env.declare("parseInt", JSNativeFunction("parseInt", global_parse_int))
    env.declare("parseFloat", JSNativeFunction("parseFloat", global_parse_float))
    env.declare("isNaN", JSNativeFunction("isNaN", global_is_nan))
    env.declare("isFinite", JSNativeFunction("isFinite", global_is_finite))
    env.declare("setTimeout", JSNativeFunction("setTimeout", global_set_timeout))
    
    env.declare("String", JSNativeFunction("String", global_string_constructor))
    env.declare("Number", create_number_constructor())
    env.declare("Boolean", JSNativeFunction("Boolean", global_boolean_constructor))
    
    # Global String static methods (fromCharCode)
    string_ctor = JSNativeFunction("String", global_string_constructor)
    def from_char_code(interpreter, this, args):
        return "".join(chr(int(js_to_number(a))) for a in args)
    string_ctor.set("fromCharCode", JSNativeFunction("fromCharCode", from_char_code))
    env.assign("String", string_ctor)
    
    env.declare("Math", create_math_object())
    env.declare("JSON", create_json_object())
    env.declare("console", create_console_object())
    env.declare("Date", JSNativeFunction("Date", date_constructor))
    env.declare("Object", create_object_constructor())
    env.declare("Array", create_array_constructor())
    
    # NaN and Infinity as global constants
    env.declare("NaN", float('nan'), is_const=False)
    env.declare("Infinity", float('inf'), is_const=False)

