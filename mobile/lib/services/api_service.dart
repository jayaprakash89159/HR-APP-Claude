import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );
  static const _storage = FlutterSecureStorage();

  // Token management
  Future<String?> getAccessToken() async => await _storage.read(key: 'access_token');
  Future<String?> getRefreshToken() async => await _storage.read(key: 'refresh_token');

  Future<void> saveTokens(String access, String refresh) async {
    await _storage.write(key: 'access_token', value: access);
    await _storage.write(key: 'refresh_token', value: refresh);
  }

  Future<void> clearTokens() async {
    await _storage.deleteAll();
  }

  // Headers
  Future<Map<String, String>> _headers({bool withAuth = true}) async {
    final headers = {'Content-Type': 'application/json'};
    if (withAuth) {
      final token = await getAccessToken();
      if (token != null) headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  // Refresh token
  Future<bool> refreshToken() async {
    final refresh = await getRefreshToken();
    if (refresh == null) return false;

    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/auth/token/refresh/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh': refresh}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        await saveTokens(data['access'], data['refresh'] ?? refresh);
        return true;
      }
    } catch (_) {}
    return false;
  }

  // Generic GET
  Future<ApiResponse> get(String path) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl$path'),
        headers: await _headers(),
      );
      return _handleResponse(response);
    } on SocketException {
      return ApiResponse(success: false, error: 'No internet connection');
    } catch (e) {
      return ApiResponse(success: false, error: e.toString());
    }
  }

  // Generic POST
  Future<ApiResponse> post(String path, Map<String, dynamic> body) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl$path'),
        headers: await _headers(),
        body: jsonEncode(body),
      );
      return _handleResponse(response);
    } on SocketException {
      return ApiResponse(success: false, error: 'No internet connection');
    } catch (e) {
      return ApiResponse(success: false, error: e.toString());
    }
  }

  // POST with multipart (files + form data)
  Future<ApiResponse> postMultipart(
    String path,
    Map<String, String> fields, {
    File? imageFile,
    String imageField = 'selfie',
  }) async {
    try {
      final token = await getAccessToken();
      final request = http.MultipartRequest('POST', Uri.parse('$baseUrl$path'));

      if (token != null) request.headers['Authorization'] = 'Bearer $token';
      request.fields.addAll(fields);

      if (imageFile != null) {
        request.files.add(await http.MultipartFile.fromPath(imageField, imageFile.path));
      }

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      return _handleResponse(response);
    } on SocketException {
      return ApiResponse(success: false, error: 'No internet connection');
    } catch (e) {
      return ApiResponse(success: false, error: e.toString());
    }
  }

  // Response handler with auto-refresh
  ApiResponse _handleResponse(http.Response response) {
    try {
      final data = jsonDecode(response.body);
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return ApiResponse(success: true, data: data);
      } else if (response.statusCode == 400) {
        return ApiResponse(success: false, error: _extractError(data), statusCode: 400);
      } else if (response.statusCode == 401) {
        return ApiResponse(success: false, error: 'Session expired. Please login again.', statusCode: 401);
      } else if (response.statusCode == 403) {
        return ApiResponse(success: false, error: 'Access denied.', statusCode: 403);
      } else if (response.statusCode == 404) {
        return ApiResponse(success: false, error: 'Resource not found.', statusCode: 404);
      } else if (response.statusCode >= 500) {
        return ApiResponse(success: false, error: 'Server error. Please try again later.', statusCode: response.statusCode);
      }
      return ApiResponse(success: false, error: 'Unexpected error.', statusCode: response.statusCode);
    } catch (e) {
      return ApiResponse(success: false, error: 'Invalid server response');
    }
  }

  String _extractError(dynamic data) {
    if (data is Map) {
      if (data.containsKey('error')) return data['error'].toString();
      if (data.containsKey('detail')) return data['detail'].toString();
      // Field errors
      final errors = <String>[];
      data.forEach((key, value) {
        if (value is List) errors.add('$key: ${value.join(', ')}');
        else errors.add('$key: $value');
      });
      return errors.join('\n');
    }
    return data.toString();
  }
}

class ApiResponse {
  final bool success;
  final dynamic data;
  final String? error;
  final int? statusCode;

  ApiResponse({required this.success, this.data, this.error, this.statusCode});
}
