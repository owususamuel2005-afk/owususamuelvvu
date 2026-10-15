/// Greets a person by name.
String greet(String name) => 'Hello, $name!';

/// Returns the sum of two numbers.
int add(int a, int b) => a + b;

/// Returns true if n is even.
bool isEven(int n) => n % 2 == 0;

/// Returns the average of a list of numbers.
double calculateAverage(List<int> numbers) {
  int sum = 0;
  for (int n in numbers) sum += n;
  return sum / numbers.length;
}

/// Prints details with optional city.
void printDetails({required String name, required int age, String? city}) {
  print('$name, $age${city != null ? ", $city" : ""}');
}

/// Returns the largest of three numbers.
int maxOfThree(int a, int b, int c) =>
    [a, b, c].reduce((x, y) => x > y ? x : y);

/// Returns the reversed string.
String reverseString(String s) => s.split('').reversed.join();

/// Returns the smallest of three numbers.
int minOfThree(int a, int b, int c) =>
    [a, b, c].reduce((x, y) => x < y ? x : y);

/// Returns true if s reads the same forwards and backwards.
bool isPalindrome(String s) {
  String clean = s.toLowerCase();
  return clean == clean.split('').reversed.join();
}

void main() {
  print(greet('Ama'));
  print(add(5, 3));
  print(isEven(7));
  print(calculateAverage([10, 20, 30]));
  printDetails(name: 'Ama', age: 22, city: 'Accra');
  print(maxOfThree(5, 12, 8));
  print(reverseString('hello'));
  print(minOfThree(5, 12, 8));
  print(isPalindrome('madam'));
}
