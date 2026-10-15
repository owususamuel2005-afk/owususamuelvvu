class InvalidInputException implements Exception {
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
}
