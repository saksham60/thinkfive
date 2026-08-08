class JsonUtils {
  static double parseDouble(dynamic value, {double defaultValue = 0.0}) {
    if (value == null) return defaultValue;
    if (value is num) return value.toDouble();
    if (value is String) {
      return double.tryParse(value) ?? defaultValue;
    }
    return defaultValue;
  }

  static DateTime parseDateTime(dynamic value) {
    if (value == null) return DateTime.now().toUtc();
    if (value is DateTime) return value.toUtc();
    if (value is String) {
      final parsed = DateTime.tryParse(value);
      if (parsed != null) return parsed.toUtc();
    }
    if (value is int) {
      // Assuming milliseconds since epoch if it's a large number
      if (value > 1000000000000) {
        return DateTime.fromMillisecondsSinceEpoch(value, isUtc: true);
      }
      return DateTime.fromMillisecondsSinceEpoch(value * 1000, isUtc: true);
    }
    return DateTime.now().toUtc();
  }

  static List<Map<String, dynamic>> normalizeResults(dynamic payload, String preferredKey) {
    if (payload == null) return [];

    // If it's already a list, just cast its elements
    if (payload is List) {
      return payload.whereType<Map<String, dynamic>>().toList();
    }

    if (payload is Map<String, dynamic>) {
      // Check for the preferred wrapper key (e.g. 'alerts', 'cases')
      if (payload.containsKey(preferredKey) && payload[preferredKey] is List) {
        return (payload[preferredKey] as List).whereType<Map<String, dynamic>>().toList();
      }
      // Check for generic 'results' wrapper
      if (payload.containsKey('results') && payload['results'] is List) {
        return (payload['results'] as List).whereType<Map<String, dynamic>>().toList();
      }
    }

    return [];
  }

  static List<T> asList<T>(dynamic value) {
    if (value == null) return [];
    if (value is List) {
      return value.whereType<T>().toList();
    }
    return [];
  }

  static Map<String, dynamic> asMap(dynamic value) {
    if (value == null) return {};
    if (value is Map<String, dynamic>) return value;
    if (value is Map) {
      return Map<String, dynamic>.from(value);
    }
    return {};
  }
}
