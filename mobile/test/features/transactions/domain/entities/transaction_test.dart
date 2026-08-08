import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/transactions/domain/entities/transaction.dart';

void main() {
  group('TransactionEntity', () {
    test('parses date fallbacks (Test 7)', () {
      final txn1 = TransactionEntity.fromJson({
        "id": "1",
        "merchant": "A",
        "amount": 10.0,
        "datetime": "2023-01-01T12:00:00Z"
      });
      expect(txn1.timestamp, DateTime.utc(2023, 1, 1, 12));

      final txn2 = TransactionEntity.fromJson({
        "id": "2",
        "merchant": "B",
        "amount": 10.0,
        "date": "2023-02-01T12:00:00Z"
      });
      expect(txn2.timestamp, DateTime.utc(2023, 2, 1, 12));
    });

    test('merchant fallbacks', () {
      final txn1 = TransactionEntity.fromJson({
        "id": "1",
        "merchant_name": "Merchant A",
        "amount": 10.0,
      });
      expect(txn1.merchant, "Merchant A");

      final txn2 = TransactionEntity.fromJson({
        "id": "2",
        "transaction_name": "Merchant B",
        "amount": 10.0,
      });
      expect(txn2.merchant, "Merchant B");
    });
  });
}
