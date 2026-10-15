void main() {
  int score = 88;
  String grade;

  // if/else checks top to bottom, first match wins
  if (score < 0 || score > 100) {
    grade = 'Invalid';
  } else if (score >= 85) {
    grade = 'A';
  } else if (score >= 75) {
    grade = 'B';
  } else if (score >= 65) {
    grade = 'C';
  } else if (score >= 55) {
    grade = 'D';
  } else {
    grade = 'F';
  }

  // Dart 3 switch — cleaner when many options
  String gradeSwitch = switch (score) {
    < 0 || > 100 => 'Invalid',
    >= 85 => 'A',
    >= 75 => 'B',
    >= 65 => 'C',
    >= 55 => 'D',
    _ => 'F',
  };

  print('Score: $score, Grade: $grade');
  print('Switch Grade: $gradeSwitch');
}
