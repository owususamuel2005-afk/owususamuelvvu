// Part 13 — Student Management System
// Customization: duplicate-enrollment guard, duplicate-assignment guard,
// Course code uppercase validation.

mixin Evaluable {
  void submitAssignment() => print('Assignment submitted');
  void takeExam() => print('Exam taken');
}

class Course {
  final String code;
  final String title;
  final int credits;

  Course(this.code, this.title, this.credits);

  factory Course.create({
    required String code,
    required String title,
    required int credits,
  }) {
    if (code.trim().isEmpty) throw ArgumentError('Course code required');
    if (credits <= 0) throw ArgumentError('Credits must be > 0');
    return Course(code.toUpperCase(), title, credits);
  }

  @override
  String toString() => '$code ($title, ${credits} cr)';
}

abstract class Person {
  String name;
  int id;
  Person({required this.name, required this.id});
  String getRole();
}

class Student extends Person with Evaluable {
  String program;
  double gpa;
  final List<Course> courses = [];

  Student({
    required String name,
    required int id,
    required this.program,
    required this.gpa,
  }) : super(name: name, id: id);

  @override
  String getRole() => 'Student';

  void enrollIn(Course c) {
    if (courses.any((x) => x.code == c.code)) {
      throw StateError('Already enrolled in ${c.code}');
    }
    courses.add(c);
  }

  int getTotalCredits() => courses.fold(0, (sum, c) => sum + c.credits);
}

class Lecturer extends Person {
  String department;
  final List<Course> teaches = [];

  Lecturer({required String name, required int id, required this.department})
    : super(name: name, id: id);

  @override
  String getRole() => 'Lecturer';

  void assignCourse(Course c) {
    if (teaches.any((x) => x.code == c.code)) {
      throw StateError('Already teaching ${c.code}');
    }
    teaches.add(c);
  }
}

void main() {
  var c1 = Course.create(code: 'inft425', title: 'Mobile Dev', credits: 3);
  var c2 = Course.create(code: 'inft301', title: 'Databases', credits: 4);

  var stu = Student(name: 'Ama', id: 1001, program: 'CS', gpa: 3.8);
  var lec = Lecturer(name: 'Dr. Adjei', id: 2001, department: 'CS');

  stu.enrollIn(c1);
  stu.enrollIn(c2);
  lec.assignCourse(c1);
  lec.assignCourse(c2);

  print('${stu.getRole()}: ${stu.name}, credits: ${stu.getTotalCredits()}');
  print('${lec.getRole()}: ${lec.name}, teaches: ${lec.teaches}');

  stu.submitAssignment();
  stu.takeExam();

  // Duplicate guard
  try {
    stu.enrollIn(c1);
  } on StateError catch (e) {
    print('Caught: ${e.message}');
  }
}
