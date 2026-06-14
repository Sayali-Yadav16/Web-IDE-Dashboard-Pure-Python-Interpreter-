"""Extended feature tests for Thunder Runtime."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.lexer import Lexer
from runtime.parser import Parser
from runtime.interpreter import Interpreter

EXTENDED_TESTS = [
    # String comparison (lexicographic)
    ('console.log("apple" < "banana");', 'true'),
    ('console.log("z" > "a");', 'true'),
    ('console.log("abc" === "abc");', 'true'),
    # toFixed on number
    ('let n = 3.14159; console.log(n.toFixed(2));', '3.14'),
    ('console.log((1.005).toFixed(2));', '1.00'),
    # Array.from
    ('let a = Array.from("hello"); console.log(a.join("-"));', 'h-e-l-l-o'),
    ('let b = Array.from([1,2,3], x => x * 2); console.log(b.join(","));', '2,4,6'),
    # Object.assign
    ('let o = Object.assign({a:1}, {b:2}); console.log(o.a + o.b);', '3'),
    # typeof undeclared
    ('console.log(typeof undeclaredXYZ);', 'undefined'),
    # typeof declared
    ('let x = 5; console.log(typeof x);', 'number'),
    ('let s = "hi"; console.log(typeof s);', 'string'),
    # Math functions
    ('console.log(Math.sin(0));', '0'),
    ('console.log(Math.cos(0));', '1'),
    ('console.log(Math.log2(8));', '3'),
    ('console.log(Math.log10(100));', '2'),
    # Array.isArray
    ('console.log(Array.isArray([1,2]));', 'true'),
    ('console.log(Array.isArray("hi"));', 'false'),
    # flatMap
    ('let r = [1,2,3].flatMap(x => [x, x*2]); console.log(r.join(","));', '1,2,2,4,3,6'),
    # String.fromCharCode
    ('console.log(String.fromCharCode(65, 66, 67));', 'ABC'),
    # void operator
    ('console.log(void 0);', 'undefined'),
    # at() method
    ('let arr = [1,2,3]; console.log(arr.at(-1));', '3'),
    # reduceRight
    ('let res = [1,2,3,4].reduceRight((acc,v) => acc + v, 0); console.log(res);', '10'),
    # Number statics
    ('console.log(Number.isNaN(NaN));', 'true'),
    ('console.log(Number.isFinite(42));', 'true'),
    ('console.log(Number.isInteger(3.0));', 'true'),
    # Infinity global
    ('console.log(Infinity > 1000);', 'true'),
    # NaN global
    ('console.log(isNaN(NaN));', 'true'),
    # switch statement
    ('''
let day = 2;
switch (day) {
  case 1: console.log("Mon"); break;
  case 2: console.log("Tue"); break;
  default: console.log("Other");
}
''', 'Tue'),
    # for...of
    ('''
let sum = 0;
for (let v of [1,2,3,4,5]) { sum += v; }
console.log(sum);
''', '15'),
    # do...while
    ('''
let i = 0, count = 0;
do { count++; i++; } while (i < 3);
console.log(count);
''', '3'),
    # String methods
    ('console.log("hello".toUpperCase());', 'HELLO'),
    ('console.log("  hi  ".trim());', 'hi'),
    ('console.log("abc".repeat(3));', 'abcabcabc'),
    ('console.log("hello world".includes("world"));', 'true'),
    ('console.log("hello".startsWith("he"));', 'true'),
    ('console.log("hello".endsWith("lo"));', 'true'),
    # Destructuring with defaults
    ('''
const [a = 10, b = 20] = [1];
console.log(a);
console.log(b);
''', '1\n20'),
    # Object.entries + forEach
    ('''
const obj = {x: 1, y: 2};
Object.entries(obj).forEach(([k, v]) => console.log(k + "=" + v));
''', 'x=1\ny=2'),
    # Spread in function args
    ('''
function add(a, b, c) { return a + b + c; }
const nums = [1, 2, 3];
console.log(add(...nums));
''', '6'),
    # Rest parameters
    ('''
function sum(...nums) {
  return nums.reduce((a, b) => a + b, 0);
}
console.log(sum(1, 2, 3, 4, 5));
''', '15'),
]


def run_code(code):
    lexer = Lexer(code)
    tokens = lexer.scan_tokens()
    p = Parser(tokens)
    ast = p.parse()
    interp = Interpreter()
    return interp.interpret(ast)


def main():
    passed = 0
    failed = 0
    errors = 0

    print("=== Thunder Runtime Extended Feature Tests ===\n")

    for code, expected in EXTENDED_TESTS:
        label = code.strip()[:60].replace('\n', ' ')
        try:
            result = run_code(code)
            actual = result['output'].strip()
            if result.get('error'):
                print(f"  [FAIL] {label}")
                print(f"    Error: {result['error']}")
                failed += 1
            elif actual == expected:
                print(f"  [PASS] {label}")
                passed += 1
            else:
                print(f"  [FAIL] {label}")
                print(f"    Expected: {repr(expected)}")
                print(f"    Got:      {repr(actual)}")
                failed += 1
        except Exception as e:
            print(f"  [ERR ] {label}")
            print(f"    Exception: {e}")
            errors += 1

    total = passed + failed + errors
    print(f"\n{'='*50}")
    print(f"Extended Tests: {passed}/{total} passed  ({failed} failed, {errors} errors)")


if __name__ == "__main__":
    main()
