TEST_CASES = [
    {
        "id": 1,
        "name": "Odd/Even Checker",
        "code": """let num = 7;
if (num % 2 === 0) {
  console.log(num + " is Even");
} else {
  console.log(num + " is Odd");
}""",
        "expected": "7 is Odd"
    },
    {
        "id": 2,
        "name": "Triangle Pattern",
        "code": """for (let i = 1; i <= 5; i++) {
  let row = "";
  for (let j = 1; j <= i; j++) {
    row += "*";
  }
  console.log(row);
}""",
        "expected": "*\n**\n***\n****\n*****"
    },
    {
        "id": 3,
        "name": "Armstrong Number",
        "code": """function isArmstrong(num) {
  let temp = num;
  let sum = 0;
  while (temp > 0) {
    let digit = temp % 10;
    sum += digit ** 3;
    temp = Math.floor(temp / 10);
  }
  return sum === num;
}
console.log(isArmstrong(153));
console.log(isArmstrong(123));""",
        "expected": "true\nfalse"
    },
    {
        "id": 4,
        "name": "Array Reverse (with Spread)",
        "code": """let arr = [1, 2, 3, 4, 5];
let reversed = [...arr].reverse();
console.log("Original: " + arr.join(", "));
console.log("Reversed: " + reversed.join(", "));""",
        "expected": "Original: 1, 2, 3, 4, 5\nReversed: 5, 4, 3, 2, 1"
    },
    {
        "id": 5,
        "name": "Palindrome Detector",
        "code": """let str = "racecar";
let reversed = str.split("").reverse().join("");
if (str === reversed) {
  console.log(str + " is a Palindrome");
} else {
  console.log(str + " is not a Palindrome");
}""",
        "expected": "racecar is a Palindrome"
    },
    {
        "id": 6,
        "name": "Closure and Recursion (Fibonacci)",
        "code": """function makeCounter() {
  let count = 0;
  return function() {
    count++;
    return count;
  };
}
const counter = makeCounter();
console.log(counter());
console.log(counter());

function fib(n) {
  if (n <= 1) return n;
  return fib(n - 1) + fib(n - 2);
}
console.log(fib(6));""",
        "expected": "1\n2\n8"
    },
    {
        "id": 7,
        "name": "Block Scoping and Shadowing",
        "code": """let x = 10;
const y = 20;
if (true) {
  let x = 5;
  console.log(x);
  console.log(y);
}
console.log(x);""",
        "expected": "5\n20\n10"
    },
    {
        "id": 8,
        "name": "Array Callback Operations (map, filter, reduce)",
        "code": """let items = [1, 2, 3, 4];
let doubled = items.map(x => x * 2);
let filtered = doubled.filter(x => x > 5);
let sum = filtered.reduce((acc, val) => acc + val, 0);
console.log(sum);""",
        "expected": "14"
    },
    {
        "id": 9,
        "name": "Nested Object and Array Destructuring",
        "code": """const obj = { user: { name: "Alice", age: 25 }, tags: [1, 2] };
const { user: { name }, tags: [first, second] } = obj;
console.log(name + " " + first + " " + second);""",
        "expected": "Alice 1 2"
    },
    {
        "id": 10,
        "name": "Type Coercion and Comparison",
        "code": """console.log("5" + 3);
console.log("5" - 3);
console.log("5" == 5);
console.log("5" === 5);
console.log(null == undefined);
console.log(null === undefined);""",
        "expected": "53\n2\ntrue\nfalse\ntrue\nfalse"
    },
    {
        "id": 11,
        "name": "Optional Chaining and Nullish Coalescing",
        "code": """const obj = { a: { b: 2 } };
console.log(obj.a?.b);
console.log(obj.c?.d);
console.log(null ?? 42);
console.log(undefined ?? "default");
console.log(0 ?? 100);""",
        "expected": "2\nundefined\n42\ndefault\n0"
    },
    {
        "id": 12,
        "name": "Math Operations and Rounding",
        "code": """console.log(Math.max(1, 5, 3));
console.log(Math.min(1, 5, 3));
console.log(Math.round(2.5));
console.log(Math.ceil(2.1));
console.log(Math.floor(2.9));""",
        "expected": "5\n1\n3\n3\n2"
    }
]
