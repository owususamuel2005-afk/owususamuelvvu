// Part 10 — Mixins
// Customizations: added Walkable mixin, Penguin class using Swimmable+Walkable,
// and wingspan field on Flyable.

mixin Flyable {
  int wingspan = 0; // CUSTOM
  void fly() => print('Flying...');
  void land() => print('Landing...');
  bool get canFly => true;
}

mixin Swimmable {
  void swim() => print('Swimming...');
  void dive() => print('Diving...');
}

// CUSTOM: new mixin
mixin Walkable {
  void walk() => print('Walking...');
}

class Animal {
  String name;
  Animal(this.name);
  void eat() => print('$name is eating');
}

class Duck extends Animal with Flyable, Swimmable {
  Duck(String name) : super(name);
}

class Fish extends Animal with Swimmable {
  Fish(String name) : super(name);
}

class Eagle extends Animal with Flyable {
  Eagle(String name) : super(name);
}

// CUSTOM: Penguin uses all three mixins
class Penguin extends Animal with Swimmable, Walkable {
  Penguin(String name) : super(name);
}

void main() {
  var duck = Duck('Daffy')..wingspan = 40;
  var fish = Fish('Nemo');
  var eagle = Eagle('Aquila')..wingspan = 200;
  var penguin = Penguin('Pingu'); // CUSTOM

  duck.eat();
  duck.fly();
  duck.swim();

  fish.eat();
  fish.swim();
  eagle.eat();
  eagle.fly();
  penguin.eat();
  penguin.swim();
  penguin.walk();

  print('Duck canFly: ${duck.canFly}, wingspan: ${duck.wingspan}');
}
