import 'package:flutter/foundation.dart';

import 'api_service.dart';

class LeaveService extends ChangeNotifier {
  final ApiService _api;

  bool _isLoading = false;
  String? _error;
  List<Map<String, dynamic>> _types = [];
  List<Map<String, dynamic>> _balances = [];
  List<Map<String, dynamic>> _applications = [];
  List<Map<String, dynamic>> _holidays = [];

  LeaveService(this._api);

  bool get isLoading => _isLoading;
  String? get error => _error;
  List<Map<String, dynamic>> get types => _types;
  List<Map<String, dynamic>> get balances => _balances;
  List<Map<String, dynamic>> get applications => _applications;
  List<Map<String, dynamic>> get holidays => _holidays;

  Future<void> load() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final responses = await Future.wait([
        _api.get('/api/v1/leave/types/'),
        _api.get('/api/v1/leave/balances/'),
        _api.get('/api/v1/leave/applications/'),
        _api.get('/api/v1/leave/holidays/?year=${DateTime.now().year}'),
      ]);
      if (responses[0].success) _types = _asList(responses[0].data);
      if (responses[1].success) _balances = _asList(responses[1].data);
      if (responses[2].success) _applications = _asList(responses[2].data);
      if (responses[3].success) _holidays = _asList(responses[3].data);
      final failed = responses.where((response) => !response.success).toList();
      _error = failed.isEmpty ? null : failed.first.error;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> applyLeave({
    required String leaveTypeId,
    required DateTime fromDate,
    required DateTime toDate,
    required String reason,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final response = await _api.post('/api/v1/leave/applications/', {
        'leave_type_id': leaveTypeId,
        'from_date': _date(fromDate),
        'to_date': _date(toDate),
        'reason': reason.trim(),
      });
      if (!response.success) {
        _error = response.error;
        return false;
      }
      _applications = [Map<String, dynamic>.from(response.data), ..._applications];
      return true;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  List<Map<String, dynamic>> _asList(dynamic value) => value is List
      ? value.map((item) => Map<String, dynamic>.from(item as Map)).toList()
      : [];

  String _date(DateTime date) => '${date.year.toString().padLeft(4, '0')}-'
      '${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
}