import sys
import os
import traceback

# Add workspace directory to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.lexer import Lexer
from runtime.parser import Parser
from runtime.interpreter import Interpreter
from tests.test_cases import TEST_CASES

# ANSI Color codes
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

def run_code(code):
    # Lex
    lexer = Lexer(code)
    tokens = lexer.scan_tokens()
    
    # Parse
    parser = Parser(tokens)
    program = parser.parse()
    
    # Interpret
    interpreter = Interpreter()
    result = interpreter.interpret(program)
    return result

def execute_file(file_path):
    if not os.path.exists(file_path):
        print(f"{RED}Error: File '{file_path}' not found.{RESET}")
        sys.exit(1)
        
    print(f"{CYAN}Executing JS file: {file_path}{RESET}\n" + "="*50)
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()
        
    try:
        res = run_code(code)
        if res["success"]:
            if res["output"]:
                print(res["output"])
        else:
            print(f"{RED}Execution Error:{RESET}\n{res['error']}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"{RED}Internal Interpreter Error:{RESET}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

def run_official_suite():
    print(f"{BOLD}{CYAN}=== Running Thunder Runtime Official Test Cases ==={RESET}\n")
    passed_count = 0
    total_count = len(TEST_CASES)
    
    for tc in TEST_CASES:
        print(f"Running TC{tc['id']}: {BOLD}{tc['name']}{RESET}...")
        
        try:
            res = run_code(tc["code"])
            if not res["success"]:
                print(f"  [{RED}FAIL{RESET}] - Syntax/Runtime error occurred:")
                print(f"    {RED}{res['error']}{RESET}")
                continue
                
            got = res["output"].strip().replace("\r\n", "\n")
            expected = tc["expected"].strip().replace("\r\n", "\n")
            
            if got == expected:
                print(f"  [{GREEN}PASS{RESET}]")
                passed_count += 1
            else:
                print(f"  [{RED}FAIL{RESET}]")
                print(f"    Expected:\n{YELLOW}{expected}{RESET}")
                print(f"    Got:\n{RED}{got}{RESET}")
        except Exception as e:
            print(f"  [{RED}FAIL{RESET}] - Internal Interpreter Exception:")
            traceback.print_exc(limit=3)
            
        print("-" * 50)
        
    score = (passed_count / total_count) * 100
    color = GREEN if passed_count == total_count else YELLOW if passed_count > 0 else RED
    print(f"\n{BOLD}Test Summary:{RESET}")
    print(f"  Passed: {color}{passed_count}/{total_count}{RESET} cases")
    print(f"  Score:  {color}{score:.1f}%{RESET} ({passed_count * 20}/100 points)")
    
    if passed_count != total_count:
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        execute_file(sys.argv[1])
    else:
        run_official_suite()
