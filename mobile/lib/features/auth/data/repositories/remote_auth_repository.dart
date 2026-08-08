import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'dart:convert';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/api_endpoints.dart';
import '../../../../core/network/network_failure.dart';
import '../../domain/entities/user.dart';
import '../../domain/repositories/auth_repository.dart';

class RemoteAuthRepository implements AuthRepository {
  final ApiClient _apiClient;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  static const String _userCacheKey = 'cached_user';

  RemoteAuthRepository(this._apiClient);

  @override
  Future<User> login(String email, String password) async {
    try {
      await _apiClient.dio.post(
        ApiEndpoints.login,
        data: {'email': email, 'password': password},
      );

      final meResponse = await _apiClient.dio.get(ApiEndpoints.authMe);
      final user = User.fromJson(meResponse.data);
      await _storage.write(
        key: _userCacheKey,
        value: jsonEncode(user.toJson()),
      );
      return user;
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw const UnauthorizedFailure('Invalid email or password');
      }
      throw NetworkFailureMapper.fromDioException(e);
    }
  }

  @override
  Future<void> logout() async {
    try {
      await _apiClient.dio.post(ApiEndpoints.logout);
    } catch (_) {
      // Ignore errors on logout
    } finally {
      await _apiClient.cookieJar.deleteAll();
      await _storage.delete(key: _userCacheKey);
    }
  }

  @override
  Future<User?> checkSession() async {
    try {
      final response = await _apiClient.dio.get(ApiEndpoints.authMe);
      final user = User.fromJson(response.data);
      await _storage.write(
        key: _userCacheKey,
        value: jsonEncode(user.toJson()),
      );
      return user;
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        await _apiClient.cookieJar.deleteAll();
        await _storage.delete(key: _userCacheKey);
        return null;
      }
      throw NetworkFailureMapper.fromDioException(e);
    }
  }
}
