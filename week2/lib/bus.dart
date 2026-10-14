double calculateFare({
  required double distanceKm,
  required bool isPeak,
  required bool isStudent,
  required bool isSenior,
  required bool isWeekend,
}) {
  if (distanceKm < 0) throw ArgumentError('Distance cannot be negative');

  double fare = 2.50 + (distanceKm * 0.80);

  if (isPeak) fare *= 1.20; // *= means "multiply by"

  // Use the bigger discount only
  double discount = 0;
  if (isStudent) discount = 0.15;
  if (isSenior && 0.30 > discount) discount = 0.30;
  fare *= (1 - discount);

  if (isWeekend) fare *= 0.90;

  return fare;
}

void main() {
  print(
    calculateFare(
      distanceKm: 10,
      isPeak: true,
      isStudent: true,
      isSenior: false,
      isWeekend: false,
    ),
  );
}
