// ============================================================
// STUDENT MANAGEMENT SYSTEM
// Week 5 - OOP Exercise (Part 13)
// Demonstrates: abstract classes, inheritance, factory
// constructors, mixins, encapsulation, and polymorphism.
// ============================================================

// ------------------------------------------------------------
// MIXIN: Evaluable
// A mixin is reusable behaviour that can be "mixed in" to any
// class with `with`. It is NOT an is-a relationship, so it can
// be applied to Student without forcing a class hierarchy.
// ------------------------------------------------------------
mixin Evaluable {
  void submitAssignment() {
    print('Assignment submitted.');
  }

  void takeExam() {
    print('Exam taken.');
  }
}

// ------------------------------------------------------------
// CLASS: Course
// Holds a course code, title, and credit value.
// Uses a FACTORY constructor so we can validate input and
// normalise the code BEFORE returning a Course instance.
// ------------------------------------------------------------
class Course {
  final String code;
  final String title;
  final int credits;

  // Private named constructor used by the factory.
  Course._({required this.code, required this.title, required this.credits});

  // Factory constructor: validates credits and uppercases code.
  factory Course.create({
    required String code,
    required String title,
    required int credits,
  }) {
    if (credits <= 0) {
      throw ArgumentError('Course credits must be greater than 0.');
    }
    return Course._(code: code.toUpperCase(), title: title, credits: credits);
  }

  @override
  String toString() => '$code - $title ($credits credits)';
}

// ------------------------------------------------------------
// ABSTRACT CLASS: Person
// Cannot be instantiated directly. Defines the shared fields
// and forces every subclass to implement getRole().
// ------------------------------------------------------------
abstract class Person {
  final String name;
  final int id;

  Person({required this.name, required this.id});

  // Abstract method: every subclass MUST provide its own version.
  String getRole();

  // Concrete method: inherited by all subclasses.
  void describe() {
    print('$name (ID: $id) - Role: ${getRole()}');
  }
}

// ------------------------------------------------------------
// CLASS: Student
// Extends Person, adds program, gpa, and a course list.
// Mixes in Evaluable so students can submit assignments/exams.
// ------------------------------------------------------------
class Student extends Person with Evaluable {
  final String program;
  double gpa;
  final List<Course> courses = [];

  Student({
    required super.name,
    required super.id,
    required this.program,
    required this.gpa,
  });

  @override
  String getRole() => 'Student';

  // Enroll in a course, preventing duplicates by course code.
  void enrollIn(Course c) {
    final alreadyEnrolled = courses.any((course) => course.code == c.code);
    if (alreadyEnrolled) {
      print('$name is already enrolled in ${c.code}.');
      return;
    }
    courses.add(c);
    print('$name enrolled in ${c.code}.');
  }

  // Sum the credits of all enrolled courses.
  int getTotalCredits() {
    if (courses.isEmpty) return 0;
    return courses.fold(0, (sum, course) => sum + course.credits);
  }
}

// ------------------------------------------------------------
// CLASS: Lecturer
// Extends Person, adds department and a list of taught courses.
// ------------------------------------------------------------
class Lecturer extends Person {
  final String department;
  final List<Course> teaches = [];

  Lecturer({required super.name, required super.id, required this.department});

  @override
  String getRole() => 'Lecturer';

  // Assign a course to this lecturer, preventing duplicates.
  void assignCourse(Course c) {
    final alreadyTeaching = teaches.any((course) => course.code == c.code);
    if (alreadyTeaching) {
      print('$name already teaches ${c.code}.');
      return;
    }
    teaches.add(c);
    print('$name assigned to teach ${c.code}.');
  }
}

// ------------------------------------------------------------
// MAIN: Create one Student, one Lecturer, and two Courses,
// then demonstrate the system.
// ------------------------------------------------------------
void main() {
  // Create two courses using the factory constructor.
  final course1 = Course.create(
    code: 'cs101',
    title: 'Intro to Programming',
    credits: 3,
  );
  final course2 = Course.create(
    code: 'ma201',
    title: 'Discrete Mathematics',
    credits: 4,
  );

  // Create one student and one lecturer.
  final student = Student(
    name: 'Ama Mensah',
    id: 1001,
    program: 'Computer Science',
    gpa: 3.6,
  );
  final lecturer = Lecturer(
    name: 'Dr. Kobbina Amoah',
    id: 2001,
    department: 'Computer Science',
  );

  print('--- Courses ---');
  print(course1);
  print(course2);
  print('');

  print('--- Enrolment ---');
  student.enrollIn(course1);
  student.enrollIn(course2);
  student.enrollIn(course1); // duplicate - should be rejected
  print('');

  print('--- Lecturer Assignment ---');
  lecturer.assignCourse(course1);
  lecturer.assignCourse(course2);
  print('');

  print('--- People and Roles ---');
  final List<Person> people = [student, lecturer];
  for (final p in people) {
    p.describe();
  }
  print('');

  print('--- Student Total Credits ---');
  print('${student.name} has ${student.getTotalCredits()} credits.');
  print('');

  print('--- Evaluable Mixin ---');
  student.submitAssignment();
  student.takeExam();
}
