// Part 4 — Inheritance
// Customizations: Lecturer gets yearsOfExperience + isSenior();
// Student gets String level; added Administrator subclass with office.

abstract class Person {
  String name;
  int age;

  Person({required this.name, required this.age});

  // Abstract — subclasses must implement
  String role();

  // Concrete — inherited as-is
  void introduce() {
    print('My name is $name');
  }
}

class Lecturer extends Person {
  String department;
  int yearsOfExperience; // CUSTOM

  Lecturer({
    required String name,
    required int age,
    required this.department,
    required this.yearsOfExperience,
  }) : super(name: name, age: age);

  @override
  String role() => 'Lecturer';

  // CUSTOM: senior check
  bool isSenior() => yearsOfExperience > 5;
}

class Student extends Person {
  String program;
  double gpa;
  String level; // CUSTOM

  Student({
    required String name,
    required int age,
    required this.program,
    required this.gpa,
    required this.level,
  }) : super(name: name, age: age);

  @override
  String role() => 'Student';

  bool isHonors() => gpa >= 3.5;
}

// CUSTOM: third Person subclass
class Administrator extends Person {
  String office;

  Administrator({required String name, required int age, required this.office})
    : super(name: name, age: age);

  @override
  String role() => 'Administrator';
}

void main() {
  var lec = Lecturer(
    name: 'Dr. Adjei',
    age: 45,
    department: 'CS',
    yearsOfExperience: 8,
  );
  var stu = Student(
    name: 'Ama',
    age: 22,
    program: 'CS',
    gpa: 3.8,
    level: '300',
  );

  // Introduce + role
  lec.introduce();
  print('Role: ${lec.role()}');
  stu.introduce();
  print('Role: ${stu.role()}');

  // isHonors on Student only
  print('${stu.name} honors? ${stu.isHonors()}');

  // Custom: isSenior on Lecturer
  print('${lec.name} senior? ${lec.isSenior()}');

  // Custom: 2nd Lecturer + 2nd Student + Administrator
  var lec2 = Lecturer(
    name: 'Dr. Owusu',
    age: 38,
    department: 'information technology',
    yearsOfExperience: 3,
  );
  var stu2 = Student(
    name: 'Kwame',
    age: 20,
    program: 'IT',
    gpa: 3.2,
    level: '200',
  );
  var admin = Administrator(name: 'Mr. Kobbina', age: 40, office: 'Room 12');

  lec2.introduce();
  stu2.introduce();
  admin.introduce();
  print('Admin role: ${admin.role()}');
}
