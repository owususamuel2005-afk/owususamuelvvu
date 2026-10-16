// lib/collections_methods.dart
// Practice file demonstrating common iterable/collection methods in Dart.

void main() {
  // 1. Create a List<int> of numbers
  List<int> numbers = [14, 3, 27, 9, 42, 6, 18, 33];
  print("Original numbers: $numbers");

  // 2. .map() — transforms each element and returns a lazy Iterable.
  //    Call .toList() to materialize it into a List.
  List<int> doubled = numbers.map((n) => n * 2).toList();
  print("\nDoubled via .map(): $doubled");

  // 3. .where() — filters elements that satisfy a condition (lazy Iterable).
  List<int> greaterThan10 = numbers.where((n) => n > 10).toList();
  print("Numbers > 10 via .where(): $greaterThan10");

  // 4. .reduce() — combines all elements into one value using the first
  //    element as the initial accumulator.
  int sum = numbers.reduce((a, b) => a + b);
  print("\nSum via .reduce(): $sum");

  // 5. .fold() — like reduce, but lets you specify an initial value (200 here).
  int sumFrom200 = numbers.fold(200, (a, b) => a + b);
  print("Sum via .fold(200, ...): $sumFrom200");

  // 6. .any() — returns true if AT LEAST ONE element matches the condition.
  bool anyOver15 = numbers.any((n) => n > 15);
  print("\nAny number > 15? $anyOver15");

  // 7. .every() — returns true only if ALL elements match the condition.
  bool allPositive = numbers.every((n) => n > 0);
  print("Every number > 0? $allPositive");

  // 8. .firstWhere() — returns the first element matching the condition.
  //    Without orElse, it throws StateError if no match is found.
  int firstOver10 = numbers.firstWhere((n) => n > 10, orElse: () => -1);
  print("\nFirst number > 10: $firstOver10");

  // 9. .take(n) — returns the first n elements as a lazy Iterable.
  List<int> firstThree = numbers.take(3).toList();
  print("\nFirst 3 via .take(3): $firstThree");

  // 10. .skip(n) — returns all elements AFTER skipping the first n.
  List<int> afterThree = numbers.skip(3).toList();
  print("After skipping 3 via .skip(3): $afterThree");

  // 11. Sort ascending — .sort() mutates the list IN PLACE.
  //     We copy first so we can still demo descending sort below.
  List<int> ascending = List.from(numbers)..sort();
  print("\nSorted ascending: $ascending");

  // 12. Sort descending — pass a custom comparator.
  //     (a, b) => b.compareTo(a) reverses the natural order.
  List<int> descending = List.from(numbers)..sort((a, b) => b.compareTo(a));
  print("Sorted descending: $descending");

  // Note: original 'numbers' list is unchanged because we sorted copies.
  print("\nOriginal still intact: $numbers");
}
