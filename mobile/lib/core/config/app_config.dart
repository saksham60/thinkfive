class AppConfig {
  static const bool useFixtures = bool.fromEnvironment(
    'USE_FIXTURES',
    defaultValue: false,
  );
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://thinkfive.onrender.com',
  );
}
