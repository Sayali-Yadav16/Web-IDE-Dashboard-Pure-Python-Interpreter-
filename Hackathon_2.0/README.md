# ⚡ Thunder Runtime

A pure Python-based JavaScript interpreter and execution environment featuring a modern, dark terminal-themed web interface. Designed and built for a Hackathon project to execute JavaScript code without Node.js, Deno, or V8 engines.

---

## 🚀 Getting Started

### 1. Installation
Thunder Runtime only requires Python 3.10+ and Flask. Install dependencies using:
```bash
pip install flask
```

### 2. Run the Web Server
Launch the Flask development server:
```bash
python app.py
```
After starting, open your browser and navigate to:
```
http://localhost:5000
```

### 3. Run CLI Tests
To execute the official 5 test cases and view the score:
```bash
python tests/run_tests.py
```
<img width="950" height="415" alt="image" src="https://github.com/user-attachments/assets/08d23929-eecb-4aaa-8190-029d14b2bcdf" />

<img width="950" height="419" alt="image" src="https://github.com/user-attachments/assets/cd9e0da1-073c-4eb1-bce8-5a6379dde7a1" />

To run any custom JavaScript file directly in your terminal:
```bash
python tests/run_tests.py path/to/file.js
```

---

## 🏛️ Architecture Overview
Thunder Runtime operates as a tree-walk interpreter structured as follows:

```
Source Code (JS String) ──> Lexer ──> Tokens ──> Parser ──> AST ──> Interpreter (Evaluator)
```

1. **Lexer (`runtime/lexer.py`)**: A character-by-character scanner that filters whitespace and comments, matches multi-character operators (`===`, `!==`, `?.`, `??`, `**`), and leverages a brace-depth stack to correctly boundary template literal (`${...}`) expression insertions.
2. **Parser (`runtime/parser.py`)**: A recursive-descent parser building a structured Abstract Syntax Tree (AST). It incorporates standard operator precedence (from Primary/Call up to Ternary and Assignment) and parses complex patterns like destructuring arrays and objects.
3. **Environment (`runtime/environment.py`)**: Represents scopes (lexical environments) with outer-scope parenting. Enforces block-scoping rules for `let` and `const` and throws ReferenceErrors or TypeErrors on invalid assignments.
4. **JS Objects & Built-ins (`runtime/js_objects.py`, `runtime/js_builtins.py`)**:
   - `JSObject`: Base class supporting property dot/bracket accessor syntax.
   - `JSArray`: Extends `JSObject` wrapping Python lists to implement **22** array methods (`push`, `pop`, `shift`, `unshift`, `slice`, `splice`, `concat`, `includes`, `indexOf`, `sort`, `reverse`, `join`, `map`, `filter`, `reduce`, `find`, `findIndex`, `some`, `every`, `forEach`, `flat`, `fill`).
   - `JSFunction` & `JSNativeFunction`: Support custom property assignments, parameter binding, default parameters, rest arguments, and closures.
   - Interceptors for primitive types (like JS String methods `.split()`, `.substring()`, `.slice()`, etc.).
5. **Interpreter (`runtime/interpreter.py`)**: Performs tree-walk evaluation. It implements JavaScript type coercion rules, loose equality comparison, logical short-circuiting, destructuring bindings, and utilizes Python runtime control flow exceptions (`ReturnException`, `BreakException`, `ContinueException`) to route JS control structures (`return`, `break`, `continue`).

---

## 🌟 Supported JavaScript Features

- **Variables & Scoping**: `let`, `const` block-scoping.
- **Data Types**: number (represented as float), string, boolean, `null`, `undefined` (with full type-coercion compatibility).
- **Operators**: Arithmetic (`+ - * / % **`), Assignment (`= += -= *= /= %=`), Logical (`&& || !`), Comparison (`== != === !== < > <= >=`), Ternary (`? :`), Nullish coalescing (`??`), and Optional Chaining (`?.`).
- **Control Flow**: `if/else`, `switch/case/break/default`, `for`, `while`, `do...while`, `break`, `continue`.
- **Loops Extra**: `for...of` array iterations and `for...in` object key reflections.
- **Functions & Closures**: Function declarations, expressions, lexical closures, recursion, and arrow functions (`(x) => x * 2`).
- **Destructuring**: Array destructuring (`const [a, b] = arr`) and Object destructuring (`const {x, y} = obj`).
- **APIs**:
  - `Math` (floor, ceil, round, abs, sqrt, pow, max, min, log, PI, E, random, trunc, sign).
  - `Date` (`new Date()`, `getFullYear()`, `getMonth()`, `getDate()`, etc.).
  - `JSON` (`JSON.stringify()`, `JSON.parse()`).
  - `Object` (`Object.keys()`, `Object.values()`, `Object.entries()`).
  - `console` (`log`, `warn`, `error` captured in execution output buffer).
  - Globals (`parseInt()`, `parseFloat()`, `isNaN()`, `isFinite()`, `setTimeout` as synchronous execution, casting wrappers `String()`, `Number()`, `Boolean()`).
