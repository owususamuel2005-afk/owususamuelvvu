void main() {
  var name = 'Owusu Samuel'; // BUG 1: missing semicolon
  int age = 22; // BUG 2: missing semicolon
  final double gpa = 3.75;
  const pi = 3.14;
  //pi = 3.14159; // BUG 3: can't change const
  //gpa = 3.80; // BUG 4: can't change final
  print('Name: $name');
  print('Age: $age');
  print('GPA: $gpa');
  print('Pi: $pi');
  print('Next year I will be ${age + 1}'); // BUG 5: missing {}
}
