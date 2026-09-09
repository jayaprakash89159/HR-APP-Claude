import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import 'api_service.dart';
import '../utils/pdf_opener_stub.dart'
  if (dart.library.io) '../utils/pdf_opener_io.dart';

class PayslipService extends ChangeNotifier {
  final ApiService _api;
  bool _isLoading = false;
  String? _error;
  List<Map<String, dynamic>> _payslips = [];
  Map<String, dynamic>? _selected;

  PayslipService(this._api);

  bool get isLoading => _isLoading;
  String? get error => _error;
  List<Map<String, dynamic>> get payslips => _payslips;
  Map<String, dynamic>? get selected => _selected;

  Future<void> load({int? year}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final suffix = year == null ? '' : '?year=$year';
      final response = await _api.get('/api/v1/payroll/payslips/$suffix');
      if (response.success && response.data is List) {
        _payslips = (response.data as List)
            .map((item) => Map<String, dynamic>.from(item as Map))
            .toList();
      } else if (!response.success) {
        _error = response.error;
      }
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> loadDetail(String id) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final response = await _api.get('/api/v1/payroll/payslips/$id/');
      if (response.success) {
        _selected = Map<String, dynamic>.from(response.data as Map);
      } else {
        _error = response.error;
      }
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> openPdf(String id) async {
    final token = await _api.getAccessToken();
    if (token == null) return false;
    final response = await http.get(
      Uri.parse('${ApiService.baseUrl}/api/v1/payroll/payslips/$id/pdf/'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode < 200 || response.statusCode >= 300) return false;
    return openPdfBytes(response.bodyBytes, 'payslip_$id.pdf');
  }
}
