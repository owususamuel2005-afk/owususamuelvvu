## Week 3 - Debugging
- **Error:** Missing semicolon
- **Prompt used:** Why is Dart saying expected ';' here?
- **AI's fix:** Add `;` after the line
- **Did it work?** Yes
- **What I learned:** Every Dart statement ends with ;

## Week 3 - Debugging 2
- **Error:** Wrong return type
- **Prompt used:** Why does Dart say String can't be returned as int?
- **AI's fix:** Change String back to int
- **Did it work?** Yes
- **What I learned:** Return type must match what you return

## Week 3 - Debugging 3
- **Error:** Too many arguments
- **Prompt used:**  Why does Dart say too many positional arguments?
- **AI's fix:** Remove extra argument
- **Did it work?** Yes
- **What I learned:** Functions take exact number of arguments

## Week 3 — Debugging

- **Error:** 
```
Error: Invalid argument(s): Cannot divide by zero
Error: InvalidInputException: Negative input not allowed
```
- **Prompt used:** "I am getting this error in my Dart program: Error: Invalid argument(s): Cannot divide by zero
Error: InvalidInputException: Negative input not allowed.
 Here is the relevant code: class InvalidInputException implements Exception {
  final String message;
  InvalidInputException(this.message);
  @override
  String toString() => 'InvalidInputException: $message';
}

double divide(int a, int b) {
  if (a < 0 || b < 0) {
    throw InvalidInputException('Negative input not allowed');
  }
  if (b == 0) {
    throw ArgumentError('Cannot divide by zero');
  }
  return a / b;
}

void main() {
  List<List<int>> pairs = [
    [10, 2],
    [10, 0],
    [-5, 2],
  ];

  for (var pair in pairs) {
    try {
      print('${pair[0]} / ${pair[1]} = ${divide(pair[0], pair[1])}');
    } catch (e) {
      print('Error: $e');
    } finally {
      print('Calculation complete');
    }
  }
}. What is causing this error, and how do I fix it? Explain the fix so I can avoid it next time."

- **AI's fix:** Said my `catch` block was printing those lines, so it wasn't a crash, and the check order was wrong
- **Did it work?** Yes
- **What I learned:** An Error: line isn't always a crash


###  Week 3 — Code Review 

Code reviewed: A Dart program with 7 required functions (greet, add, isEven, calculateAverage, printDetails, maxOfThree, reverseString) plus 2 custom functions (minOfThree, isPalindrome), each with doc comments, and a main() that calls them all.

AI's suggestions: Add a guard in calculateAverage to return 0 for an empty list; use explicit comparisons in maxOfThree/minOfThree; lowercase the input in isPalindrome before comparing.

Which I applied: All three.

Result: Yes — the code handles edge cases better and the logic is easier to read.

What I learned: Always guard against edge cases like empty lists, and normalize input before comparing strings.