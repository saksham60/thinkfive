import 'package:dio/dio.dart';
import 'package:dio_cookie_manager/dio_cookie_manager.dart';
import 'package:cookie_jar/cookie_jar.dart';
import 'package:path_provider/path_provider.dart';
import '../config/app_config.dart';

class ApiClient {
  late final Dio _dio;
  late final PersistCookieJar _cookieJar;
  bool _initialized = false;

  Future<void> init() async {
    if (_initialized) return;

    final dir = await getApplicationDocumentsDirectory();
    _cookieJar = PersistCookieJar(
      storage: FileStorage("${dir.path}/.cookies/"),
    );

    _dio = Dio(
      BaseOptions(
        baseUrl: AppConfig.apiBaseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 30),
        validateStatus: (status) => status != null && status < 400,
      ),
    );

    _dio.interceptors.add(CookieManager(_cookieJar));

    // Add simple logger
    _dio.interceptors.add(
      LogInterceptor(
        request: true,
        requestHeader: true,
        requestBody: true,
        responseHeader: false,
        responseBody: false,
        error: true,
      ),
    );

    _initialized = true;
  }

  Dio get dio {
    if (!_initialized) {
      throw StateError("ApiClient must be initialized before use.");
    }
    return _dio;
  }

  PersistCookieJar get cookieJar {
    if (!_initialized) {
      throw StateError("ApiClient must be initialized before use.");
    }
    return _cookieJar;
  }
}
