// Part 14 — Debug Blind (FIXED version)
// Bugs found and fixed: Dog super call, missing braces, @Override -> @override,
// abstract method syntax, Sname typo, Animal() missing arg.

class Animal {
  String name;
  Animal(this.name);

  void speak() {
    print('Some sound');
  }
}

class Dog extends Animal {
  Dog(String name) : super(name); // FIX: call super

  @override // FIX: lowercase @override
  void speak() {
    print('$name says Woof');
  }
}

abstract class Pet {
  void play(); // FIX: no 'abstract' keyword before method in Dart
}

class Cat extends Pet {
  String name;
  Cat(this.name);

  @override
  void play() {
    print('$name is playing'); // FIX: $name not Sname
  }
}

void main() {
  var dog = Dog('Rex');
  dog.speak();

  var cat = Cat('Whiskers');
  cat.play();

  var a = Animal('Generic'); // FIX: pass name
  a.speak();
}
