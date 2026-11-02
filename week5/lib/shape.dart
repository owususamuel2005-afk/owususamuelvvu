// Part 6 — Abstract Classes & Interfaces
// Customizations: added Square (extends Rectangle), Cube (extends Shape
// with volume()), and a `unit` getter on Shape.

import 'dart:math';

abstract class Shape {
  // Abstract methods — no body
  double area();
  double perimeter();

  // Concrete method — inherited
  String describe() => 'I am a $runtimeType';

  // CUSTOM: unit getter
  String get unit => 'cm²';
}

class Circle implements Shape {
  double radius;
  Circle(this.radius);

  @override
  double area() => pi * radius * radius;

  @override
  double perimeter() => 2 * pi * radius;

  @override
  String describe() => 'I am a Circle';

  @override
  String get unit => 'cm²';
}

class Rectangle implements Shape {
  double width, height;
  Rectangle(this.width, this.height);

  @override
  double area() => width * height;

  @override
  double perimeter() => 2 * (width + height);

  @override
  String describe() => 'I am a Rectangle';

  @override
  String get unit => 'cm²';
}

class Triangle implements Shape {
  double base, height, sideA, sideB;
  Triangle(this.base, this.height, this.sideA, this.sideB);

  @override
  double area() => 0.5 * base * height;

  @override
  double perimeter() => base + sideA + sideB;

  @override
  String describe() => 'I am a Triangle';

  @override
  String get unit => 'cm²';
}

// CUSTOM: Square extends Rectangle
class Square extends Rectangle {
  Square(double side) : super(side, side);

  @override
  String describe() => 'I am a Square';
}

// CUSTOM: Cube extends Shape with volume
class Cube extends Shape {
  double side;
  Cube(this.side);

  @override
  double area() => 6 * side * side;

  @override
  double perimeter() => 12 * side;

  @override
  String describe() => 'I am a Cube';

  @override
  String get unit => 'cm²';

  double volume() => side * side * side;
}

void main() {
  var c = Circle(5);
  var r = Rectangle(4, 6);
  var t = Triangle(3, 4, 5, 5);
  var sq = Square(3); // CUSTOM
  var cube = Cube(2); // CUSTOM

  for (var s in <Shape>[c, r, t, sq, cube]) {
    print(
      '${s.describe()} — area: ${s.area().toStringAsFixed(2)} ${s.unit}, '
      'perimeter: ${s.perimeter().toStringAsFixed(2)}',
    );
  }

  print('Cube volume: ${cube.volume()} cm³');
}
