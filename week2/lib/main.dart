void main() {
  var name = 'Owusu Samuel'; // name 
  int age = 22; // age
  final double gpa = 3.75; 
  const pi = 3.14;
  //pi = 3.14159; 
  //gpa = 3.80; 
  print('Name: $name');
  print('Age: $age');
  print('GPA: $gpa');
  print('Pi: $pi');
  print('Next year I will be ${age + 1}'); // BUG 5: missing {}
}
