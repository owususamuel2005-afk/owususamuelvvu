// Part 2 — Classes & Objects (customized)
// Customizations: added List<String> courses field, addCourse() method,
// honors threshold changed 3.5 -> 3.3, added initials getter.

class Student {
  // Fields
  String name;
  int age;
  String program;
  double gpa;
  List<String> courses; // CUSTOM: new field

  // Constructor with named parameters
  Student({
    required this.name,
    required this.age,
    required this.program,
    required this.gpa,
    List<String>? courses, // optional, defaults to empty
  }) : courses = courses ?? [];

  // CUSTOM: add a course
  void addCourse(String course) {
    courses.add(course);
  }

  // Print student details
  void displayInfo() {
    print('Name: $name');
    print('Age: $age');
    print('Program: $program');
    print('GPA: $gpa');
    print('Courses: $courses');
    print('---');
  }

  // Honors check — custom threshold 3.3
  bool isHonors() => gpa >= 3.3;

  // Getter: age in months
  int get ageInMonths => age * 12;

  // CUSTOM: initials getter (first letter of each name part)
  String get initials {
    return name
        .trim()
        .split(RegExp(r'\s+'))
        .map((part) => part.isEmpty ? '' : part[0].toUpperCase())
        .join();
  }

  // toString override
  @override
  String toString() => 'Student: $name';
}

void main() {
  // Create three students
  var s1 = Student(name: 'Ama Mensah', age: 22, program: 'CS', gpa: 3.8);
  var s2 = Student(name: 'Kwame Boateng', age: 21, program: 'IT', gpa: 3.1);
  var s3 = Student(name: 'Efua Owusu', age: 23, program: 'SE', gpa: 3.4);

  // 1. Print details
  s1.displayInfo();
  s2.displayInfo();
  s3.displayInfo();

  // 2. Honors status
  print('${s1.name} honors? ${s1.isHonors()}');
  print('${s2.name} honors? ${s2.isHonors()}');
  print('${s3.name} honors? ${s3.isHonors()}');

  // 3. Age in months
  print('${s1.name}: ${s1.ageInMonths} months');
  print('${s2.name}: ${s2.ageInMonths} months');
  print('${s3.name}: ${s3.ageInMonths} months');

  // 4. toString
  print(s1);
  print(s2);
  print(s3);

  // CUSTOM: initials
  print('${s1.name} initials: ${s1.initials}');

  // Test customization: add course to a student
  s3.addCourse('INFT425');
  print('${s3.name} courses after adding: ${s3.courses}');
}
