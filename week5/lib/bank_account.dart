// Part 8 — Encapsulation
// Customizations: owner setter (rejects empty), overdraft limit,
// transaction history list.

class BankAccount {
  double _balance = 0;
  String _owner;
  double _overdraftLimit; // CUSTOM
  final List<String> _transactions = []; // CUSTOM

  BankAccount(this._owner, {double overdraftLimit = 0})
    : _overdraftLimit = overdraftLimit;

  double get balance => _balance;
  String get owner => _owner;
  double get overdraftLimit => _overdraftLimit;
  List<String> get transactions => List.unmodifiable(_transactions);

  // CUSTOM: owner setter with validation
  set owner(String value) {
    if (value.trim().isEmpty) {
      throw ArgumentError('Owner name cannot be empty');
    }
    _owner = value;
    _transactions.add('Owner changed to $value');
  }

  void deposit(double amount) {
    if (amount <= 0) {
      throw ArgumentError('Deposit amount must be positive');
    }
    _balance += amount;
    _transactions.add('Deposited: \$$amount, New balance: \$_balance');
    print('Deposited: \$$amount, New balance: \$_balance');
  }

  void withdraw(double amount) {
    if (amount <= 0) {
      throw ArgumentError('Withdraw amount must be positive');
    }
    // CUSTOM: allow going negative up to overdraft limit
    if (_balance - amount < -_overdraftLimit) {
      throw StateError(
        'Insufficient funds. Balance: \$_balance, Overdraft: \$_overdraftLimit',
      );
    }
    _balance -= amount;
    _transactions.add('Withdraw: \$$amount, New balance: \$_balance');
    print('Withdraw: \$$amount, New balance: \$_balance');
  }

  void transfer(BankAccount other, double amount) {
    if (other == this) {
      throw ArgumentError('Cannot transfer to self');
    }
    withdraw(amount);
    other.deposit(amount);
    _transactions.add('Transferred \$$amount to ${other.owner}');
  }
}

void main() {
  var a = BankAccount('Ama', overdraftLimit: 50);
  var b = BankAccount('Kwame');

  a.deposit(100);
  a.withdraw(30);
  a.transfer(b, 20);

  try {
    a.withdraw(999999);
  } on StateError catch (e) {
    print('Caught: ${e.message}');
  }

  print('A balance: ${a.balance}, B balance: ${b.balance}');
  print('A transactions: ${a.transactions}');

  // Test owner setter
  try {
    b.owner = '   ';
  } on ArgumentError catch (e) {
    print('Caught: ${e.message}');
  }
  b.owner = 'Kofi';
  print('B owner after set: ${b.owner}');
}
