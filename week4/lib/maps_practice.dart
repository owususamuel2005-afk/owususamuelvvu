// lib/maps_practice.dart
// Practice file demonstrating common Map<String, int> operations in Dart.

void main() {
  // 1. Create a Map<String, int> mapping horror movies to release years
  Map<String, int> movieYears = {
    "The Shining": 1980,
    "Hereditary": 2018,
    "Get Out": 2017,
    "The Thing": 1982,
    "Alien": 1979,
  };

  // 2. Print the entire map
  print("Full map: $movieYears");

  // 3. Print the keys and values separately
  print("Keys:   ${movieYears.keys}");
  print("Values: ${movieYears.values}");

  // 4. Add a new movie-year pair
  movieYears["The Witch"] = 2015;
  print("\nAfter adding 'The Witch': $movieYears");

  // 5. Remove a movie by key
  movieYears.remove("The Thing");
  print("After removing 'The Thing': $movieYears");

  // 6. Check if a key exists using .containsKey()
  bool hasAlien = movieYears.containsKey("Alien");
  print("\nContains key 'Alien'? $hasAlien");

  // 7. Check if a value exists using .containsValue()
  bool has1980 = movieYears.containsValue(1980);
  print("Contains value 1980? $has1980");

  // 8. Update "Get Out" to a different year
  // (Just to show how assignment overwrites an existing key's value.)
  movieYears["Get Out"] = 2018;
  print("\nAfter updating 'Get Out' to 2018: ${movieYears["Get Out"]}");

  // 9. Iterate over the map and print "Title (Year)" for each entry
  print("\nAll movies:");
  movieYears.forEach((title, year) {
    print("$title ($year)");
  });

  // 10. Print the length of the map
  print("\nMap length: ${movieYears.length}");
}
