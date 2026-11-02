Prompt Log — Mobile Application Development
Week 5 — OOP Exercises


Part 2 — Classes and Objects
Base prompt: Write a Dart program with a Student class (fields name, age, program, gpa; named-parameter constructor; displayInfo(); isHonors() if gpa == 3.5; ageInMonths getter; toString() returning "Student: [name]"). Create three students in main() and print details, honors status, age in months, and toString(). Add comments.

My customizations: added List<String> courses + addCourse(), threshold 3.5 → 3.3, added initials getter

What worked: All three students printed correctly, honors check used 3.3, initials returned the first letters.

What broke / what I fixed: Forgot required on name → got "non-nullable variable must be initialized". Added required to all fields. Also updated isHonors() to use 3.3.



Part 3 — Break It: Classes
Missing required name → error: The non-nullable variable 'name' must be initialized.

_name private access → error: _name is private and not accessible outside the class.

Wrong constructor param grade: → error: grade is not a parameter of the constructor.

Missing required arg → error: a required named parameter is missing.

Nullable method call → error: cannot call methods on a nullable variable without a null check.



Part 4 — Inheritance
My customizations: Lecturer yearsOfExperience + isSenior(); Student level; Administrator subclass

What I learned: A subclass must call super(...) for the parent constructor. It inherits concrete methods (introduce()) and must override abstract ones (role()). A Person reference can only see Person members, so child-only methods need a cast.



Part 5 — Break It: Inheritance
Removed super call → error: the superclass constructor requires arguments.

Removed role() from Student → error: the class must implement the abstract method role().

int role() return-type mismatch → error: the return type doesn't match the parent method.

p.isHonors() on Person → error: isHonors is not defined for the type Person.

Multiple extends → error: Dart does not support multiple inheritance.



Part 6 — Abstract & Interfaces
My customizations: Square, Cube with volume(), unit getter

What I learned: extends shares implementation; implements only takes the interface and forces every member to be written. Adding unit to Shape broke all implements classes until each declared it. Abstract classes can't be instantiated.


Part 7 — Break It: Abstract
Deleted area() from Circle → error: the class must implement the abstract method area.

Shape() instantiation → error: abstract classes cannot be instantiated.

extends Shape in Circle → error: the class must implement area and perimeter.

int area() → error: the return type doesn't match the interface.



Part 8 — Encapsulation (BankAccount)
My customizations: owner setter with validation, overdraft, transaction history

What I learned: Private fields can only be reached through getters, setters, and methods. Validation belongs inside the setter/method (ArgumentError, StateError) so callers can't bypass it. try/catch turns thrown errors into handled messages.



Part 9 — Break It: Encapsulation
account._balance = 1000000; → error: _balance is private and not accessible outside the class.

account.deposit(-50); → ArgumentError thrown; crashes if uncaught. Fixed with try/catch.

account.withdraw(999999); → StateError thrown; wrapped in try/catch.

Public field owner = '' → no, a plain field has no validation. Fixed by making it private with a validating setter.



Part 10 — Mixins
Base prompt: mixins Flyable (fly(), land(), canFly), Swimmable (swim(), dive()), base class Animal (name, eat()), Duck with Flyable, Swimmable, Fish with Swimmable, Eagle with Flyable. Create one of each and call the right methods. Add comments.

My customizations: new mixin Walkable with walk(); Penguin extends Animal with Swimmable, Walkable; int wingspan in Flyable

What I learned: Mixins are reusable behaviour applied with with — composition, not inheritance. A class can stack several mixins, and the last one in the list wins on duplicate methods.




Part 11 — Break It: Mixins
class Flyable used with with → error: a class without a constructor cannot be used as a mixin.

eagle.swim(); → error: swim is not defined for the type Eagle.

Duplicate fly() in two mixins → the last mixin wins; mixin order matters.



Part 12 — AI Code Review
Weak prompt: Review this Dart code. → AI rewrote the class and gave style tips; found 0 real bugs.

Strong prompt: senior-reviewer prompt with 5 criteria, "do NOT rewrite", severity labels. → AI named concrete issues, pointed to lines, prioritised HIGH/MEDIUM/LOW, output was usable.

Issues I agreed with:

HIGH: transfer() does not null-check other, so passing null crashes at other.deposit(...) instead of failing cleanly.

MEDIUM: withdraw() appends to _transactions before the balance/overdraft check, so a rejected withdrawal still leaves a history entry.

LOW: deposit() and withdraw() print with slightly different formats (Deposited: vs Withdraw:), which is inconsistent.

Issues I rejected:

AI suggested making _balance public "for easier testing". I rejected it because exposing balance directly lets any caller bypass deposit/withdraw validation — that defeats the whole purpose of the encapsulation exercise.

Issue the AI missed:

transfer() calls withdraw(amount) on the sender and then deposit(amount) on the receiver, but it never re-checks the overdraft limit after the sender's balance changes. A transfer can push the sender past -overdraftLimit when called through transfer() even though a direct withdraw() would have thrown StateError.

What I learned: A role-based, criteria-driven prompt that forbids rewriting produces an actionable review I can verify line by line; a vague prompt produces a rewrite.



Part 13 — Student Management System
My prompt: "Write a Dart program for a university student management system: (1) abstract class Person with name, id, abstract getRole(); (2) Student extends Person with program, gpa, List<Course> courses, enrollIn(Course c), getTotalCredits(); (3) Lecturer extends Person with department, List<Course> teaches, assignCourse(Course c); (4) Course with code, title, credits, and factory Course.create(...); (5) mixin Evaluable with submitAssignment() and takeExam(), applied to Student. In main(), create one Student, one Lecturer, two Courses and demonstrate. Add comments explaining the design."



Part 14 — Debug Blind
Bugs I found without AI:

Dog constructor doesn't call super(name) — assigns this.name directly.

abstract void play(); inside abstract class Pet — invalid modifier on a method.

Cat doesn't @override play() properly.

Animal a = Animal(); — no no-arg constructor exists.

main() nested inside Cat — should be top-level.

'Sname is playing' — typo, should be '$name is playing'.

My AI prompt: "This is a Dart OOP exercise on inheritance and abstract classes. Identify every compile-time and runtime bug, explain why each is a bug, and do NOT rewrite the code — list issues with line references only."

Comparison:

I found on my own: 6 bugs (listed above).

AI found: 4 bugs — the missing super(name) call in Dog, the invalid abstract method modifier in Pet, the missing @override in Cat, and the Animal() call with no no-arg constructor.

AI missed: the 'Sname is playing' string typo (should be '$name is playing') and the fact that main() is nested inside Cat instead of being top-level.

AI found that I had also caught: the missing super call — I had already flagged it, but the AI explained the consequence (parent field never initialised) more clearly than I did.

Lesson: reading line by line catches small details the AI skips — especially typos and structural mistakes that don't break the type system.