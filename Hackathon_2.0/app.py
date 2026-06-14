import time
import os
import traceback
from flask import Flask, request, jsonify, send_from_directory

from runtime.lexer import Lexer
from runtime.parser import Parser
from runtime.interpreter import Interpreter

app = Flask(__name__, static_folder="static", static_url_path="")

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/run", methods=["POST"])
def run_code():
    data = request.get_json() or {}
    code = data.get("code", "")
    
    start_time = time.perf_counter()
    
    try:
        # 1. Lex
        lexer = Lexer(code)
        tokens = lexer.scan_tokens()
        
        # 2. Parse
        parser_obj = Parser(tokens)
        program = parser_obj.parse()
        
        # 3. Interpret
        interpreter = Interpreter()
        result = interpreter.interpret(program)
        
        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000.0
        
        return jsonify({
            "output": result["output"],
            "error": result["error"],
            "success": result["success"],
            "execution_time_ms": round(execution_time_ms, 2)
        })
        
    except SyntaxError as e:
        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000.0
        return jsonify({
            "output": "",
            "error": f"SyntaxError: {str(e)}",
            "success": False,
            "execution_time_ms": round(execution_time_ms, 2)
        })
    except Exception as e:
        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000.0
        # Capture internal trace for debugging in Flask stdout
        traceback.print_exc()
        return jsonify({
            "output": "",
            "error": f"InterpreterError: {str(e)}",
            "success": False,
            "execution_time_ms": round(execution_time_ms, 2)
        })

if __name__ == "__main__":
    # Standard Flask port
    app.run(host="0.0.0.0", port=5000, debug=True)
