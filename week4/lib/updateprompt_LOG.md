## Week 4 - AI-Generated Unit Tests
- **Tool used:** ChatGPT
- **What the AI generated:** Tests for add, subtract, multiply, divide, isEven, maxOfThree
- **What the AI missed:** Some boundary cases in maxOfThree and negative-number edge cases in isEven (varies by run)
- **Tests I added:** Extra tests for negative numbers, zero, and equal-value maxOfThree
- **What I learned:** AI tests usually cover happy paths; I must think about edge cases myself

## Week 4 - Code Review
- **Code reviewed:** lib/calculator.dart
- **AI's suggestions:** add parameter docs, handle negative maxOfThree better
- **Which I applied:** doc comments
- **Result:** Code was clearer
- **What I learned:** AI suggestions need verifying — not all improve the code

## Week 4 - Debug Blind
- **Bugs I found alone:** 4 out of 5
- **Bugs AI found:** 5 out of 5
- **AI found extra:** the Set deduplication misconception
- **What I learned:** Always `.toList()` after map/where; use `orElse` with `firstWhere`

## Week 4 - calculateGrade (Part 14 Challenge)
- **Prompt style used:** Context / Task / Constraints / Format
- **Tests written:** 17 (all grade levels, all boundaries, just-below boundaries, invalid inputs)
- **What I learned:** Boundary testing catches off-by-one errors AI often misses


## Week 4 - Debug Blind (Part 15)
- **Bugs I found alone:** 4 out of 5
- **Bugs AI found:** 5 out of 5
- **AI found extra:** the Set deduplication issue (I assumed duplicates were kept)
- **What I learned:** Always `.toList()` after `.map()` / `.where()`; use `orElse` with `firstWhere`; Set silently drops duplicates