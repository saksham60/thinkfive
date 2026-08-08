import 'package:dio/dio.dart';

abstract class NetworkFailure implements Exception {
  final String message;
  const NetworkFailure(this.message);

  @override
  String toString() => message;
}

class UnauthorizedFailure extends NetworkFailure {
  const UnauthorizedFailure([super.message = 'Unauthorized (401)']);
}

class ForbiddenFailure extends NetworkFailure {
  const ForbiddenFailure([super.message = 'Forbidden (403)']);
}

class BadRequestFailure extends NetworkFailure {
  const BadRequestFailure([super.message = 'Bad Request (400)']);
}

class NotFoundFailure extends NetworkFailure {
  const NotFoundFailure([super.message = 'Not Found (404)']);
}

class ServerFailure extends NetworkFailure {
  const ServerFailure([super.message = 'Backend Unavailable']);
}

class ConnectionFailure extends NetworkFailure {
  const ConnectionFailure([super.message = 'Network Unavailable']);
}

class TimeoutFailure extends NetworkFailure {
  const TimeoutFailure([super.message = 'Network Timeout']);
}

class ConflictFailure extends NetworkFailure {
  const ConflictFailure([super.message = 'Conflict (409)']);
}

class RateLimitFailure extends NetworkFailure {
  const RateLimitFailure([super.message = 'Rate Limited (429)']);
}

class UnknownNetworkFailure extends NetworkFailure {
  const UnknownNetworkFailure([super.message = 'Unknown Network Error']);
}

class NetworkFailureMapper {
  static NetworkFailure fromDioException(DioException e) {
    if (e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.sendTimeout ||
        e.type == DioExceptionType.receiveTimeout) {
      return const TimeoutFailure();
    }

    if (e.type == DioExceptionType.connectionError) {
      return const ConnectionFailure();
    }

    if (e.type == DioExceptionType.badResponse) {
      final statusCode = e.response?.statusCode;
      switch (statusCode) {
        case 400:
          return const BadRequestFailure();
        case 401:
          return const UnauthorizedFailure('Session Expired');
        case 403:
          return const ForbiddenFailure();
        case 404:
          return const NotFoundFailure();
        case 409:
          return const ConflictFailure();
        case 422:
          return const BadRequestFailure('Validation Error');
        case 429:
          return const RateLimitFailure();
        default:
          if (statusCode != null && statusCode >= 500) {
            return const ServerFailure();
          }
          return UnknownNetworkFailure('HTTP Error $statusCode');
      }
    }

    return UnknownNetworkFailure(e.message ?? 'Unknown Error');
  }
}
