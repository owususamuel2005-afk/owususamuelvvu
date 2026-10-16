// lib/lists_practice.dart
// Practice file demonstrating common List<String> operations in Dart.

void main() {
  // 1. Create a List<String> with at least 5 horror movies I actually like
  List<String> movies = [
    "The Shining",
    "Hereditary",
    "Get Out",
    "The Thing",
    "Alien",
  ];

  // 2. Print the initial list, its length, and the first and last elements
  print("Initial list: $movies");
  print("Length: ${movies.length}");
  print("First movie: ${movies.first}");
  print("Last movie: ${movies.last}");

  // 3. Add a new movie to the end using .add()
  movies.add("The Witch");
  print("\nAfter .add('The Witch'): $movies");

  // 4. Remove the first movie using .removeAt(0)
  movies.removeAt(0); // removes "The Shining"
  print("After .removeAt(0): $movies");

  // 5. Insert a new movie at position 2 using .insert(2, ...)
  movies.insert(2, "Sinister");
  print("After .insert(2, ...): $movies");

  // 6. Print the updated list
  print("\nUpdated list: $movies");
  print("Updated length: ${movies.length}");

  // 7. Use .contains() to check if "Joker" is in the list
  // (It shouldn't be, since this is a horror list!)
  bool hasJoker = movies.contains("Joker");
  print("\nContains 'Joker'? $hasJoker");

  // 8. Use .indexOf() to find the position of "Interstellar"
  // (Not in our list, so this will return -1 to demonstrate the behavior)
  int interstellarIndex = movies.indexOf("Interstellar");
  print("Index of 'Interstellar': $interstellarIndex");

  // Also demonstrate indexOf on a movie that IS in the list
  int getOutIndex = movies.indexOf("Get Out");
  print("Index of 'Get Out': $getOutIndex");

  // 9. Clear the list and print the empty list
  movies.clear();
  print("\nAfter .clear(): $movies");
  print("Final length: ${movies.length}");
}
