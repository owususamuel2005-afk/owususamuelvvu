// lib/sets_practice.dart
// Practice file demonstrating common Set operations in Dart.

void main() {
  // 1. Create a List<int> with duplicates
  List<int> numbers = [1, 2, 2, 3, 3, 3, 4, 4, 4, 4];

  // 2. Convert it to a Set<int> to remove duplicates
  // A Set only stores unique values, so duplicates are automatically dropped.
  Set<int> uniqueNumbers = numbers.toSet();

  // 3. Print the original list and the resulting set
  print("Original list: $numbers");
  print("As a set:      $uniqueNumbers");

  // 4. Create a Set<String> of at least 5 subjects
  Set<String> subjects = {"Math", "English", "Science", "History", "ICT"};
  print("\nInitial subjects: $subjects");

  // 5. Add a new subject using .add()
  subjects.add("Art");
  print("After adding 'Art': $subjects");

  // 6. Try to add a duplicate subject — Sets ignore duplicates silently
  subjects.add("Math"); // "Math" is already present, so nothing changes
  print("After trying to add duplicate 'Math': $subjects");

  // 7. Check if a subject exists using .contains()
  bool hasScience = subjects.contains("Science");
  print("\nContains 'Science'? $hasScience");
  bool hasMusic = subjects.contains("Music");
  print("Contains 'Music'?   $hasMusic");

  // 8. Remove a subject using .remove()
  // .remove() returns true if the element was found and removed, false otherwise.
  bool removed = subjects.remove("History");
  print("\nRemoved 'History'? $removed");
  print("Subjects now: $subjects");

  // 9. Use .union() to combine two sets
  // Union returns a NEW set containing all elements from both sets (no duplicates).
  Set<String> electiveSubjects = {"Music", "Drama", "Art", "ICT"};
  Set<String> allSubjects = subjects.union(electiveSubjects);
  print("\nSubjects:          $subjects");
  print("Electives:         $electiveSubjects");
  print("Union:             $allSubjects");

  // 10. Use .intersection() to find common elements
  // Intersection returns a NEW set with only the elements present in BOTH sets.
  Set<String> commonSubjects = subjects.intersection(electiveSubjects);
  print("\nIntersection:      $commonSubjects");

  // 11. Use .difference() to find elements in one set but not the other
  // Difference returns elements in the calling set that are NOT in the other set.
  Set<String> onlyInSubjects = subjects.difference(electiveSubjects);
  Set<String> onlyInElectives = electiveSubjects.difference(subjects);
  print("\nSubjects only (not in electives): $onlyInSubjects");
  print("Electives only (not in subjects): $onlyInElectives");

  // Bonus: print the lengths for clarity
  print("\nSubjects count:   ${subjects.length}");
  print("Electives count:  ${electiveSubjects.length}");
  print("Union count:      ${allSubjects.length}");
}
