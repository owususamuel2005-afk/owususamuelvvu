void main() {
  // for loop — you know how many times
  print('--- for loop: 1 to 10 ---');
  for (int i = 1; i <= 10; i++) {
    print(i);
  }

  // while loop — repeat while condition is true
  print('--- while loop: even 2 to 20 ---');
  int i = 2;
  while (i <= 20) {
    print(i);
    i += 2;
  }

  // do-while — run once, then check
  print('--- do-while: 10 down to 1 ---');
  int j = 10;
  do {
    print(j);
    j--;
  } while (j >= 1);

  // for-in — go through a list
  print('--- for-in: favorite foods ---');
  List<String> foods = ['Rice', 'Beans', 'Fufu', 'Banku', 'Jollof'];
  for (String food in foods) {
    print(food);
  }

  // sum 1 to 100
  print('--- sum 1 to 100 ---');
  int sum = 0;
  for (int k = 1; k <= 100; k++) {
    sum += k;
  }
  print('Sum = $sum');

  // nested loop for multiplication table
  print('--- multiplication table 1 to 5 ---');
  for (int a = 1; a <= 5; a++) {
    for (int b = 1; b <= 5; b++) {
      print('$a x $b = ${a * b}');
    }
  }
}
