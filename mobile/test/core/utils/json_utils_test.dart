import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/utils/json_utils.dart';

void main() {
  group('JsonUtils', () {
    test('parseDouble (Test 5 & 6)', () {
      expect(JsonUtils.parseDouble(125), 125.0);
      expect(JsonUtils.parseDouble(125.5), 125.5);
      expect(JsonUtils.parseDouble("125.50"), 125.5);
      expect(JsonUtils.parseDouble("invalid"), 0.0);
      expect(JsonUtils.parseDouble(null), 0.0);
    });

    test('parseDateTime', () {
      final now = DateTime.now();
      expect(JsonUtils.parseDateTime("2023-01-01T12:00:00Z"), DateTime.utc(2023, 1, 1, 12));
      final intMs = DateTime.utc(2023, 1, 1, 12).millisecondsSinceEpoch;
      expect(JsonUtils.parseDateTime(intMs), DateTime.utc(2023, 1, 1, 12));
      // Fallback
      expect(JsonUtils.parseDateTime(null).difference(now).inSeconds, closeTo(0, 1));
    });

    test('normalizeResults (Test 2 & 3)', () {
      // Wrapper cases
      final alertData1 = {"alerts": [{"id": 1}]};
      expect(JsonUtils.normalizeResults(alertData1, 'alerts').length, 1);

      final alertData2 = {"results": [{"id": 2}]};
      expect(JsonUtils.normalizeResults(alertData2, 'alerts').length, 1);

      final alertData3 = [{"id": 3}];
      expect(JsonUtils.normalizeResults(alertData3, 'alerts').length, 1);

      final alertDataEmpty = null;
      expect(JsonUtils.normalizeResults(alertDataEmpty, 'alerts').isEmpty, true);
    });
  });
}
