import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../services/attendance_service.dart';
import '../utils/app_theme.dart';

class AttendanceScreen extends StatefulWidget {
  const AttendanceScreen({super.key});

  @override
  State<AttendanceScreen> createState() => _AttendanceScreenState();
}

class _AttendanceScreenState extends State<AttendanceScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AttendanceService>().fetchMonthlyRecords();
    });
  }

  @override
  Widget build(BuildContext context) {
    final service = context.watch<AttendanceService>();
    return Scaffold(
      appBar: AppBar(title: const Text('My Attendance')),
      body: RefreshIndicator(
        onRefresh: service.fetchMonthlyRecords,
        child: service.monthlyRecords.isEmpty
            ? ListView(children: [SizedBox(height: 220), _EmptyAttendance()])
            : ListView.separated(
                padding: const EdgeInsets.all(16),
                itemCount: service.monthlyRecords.length,
                separatorBuilder: (_, __) => const SizedBox(height: 10),
                itemBuilder: (_, index) => _AttendanceTile(record: service.monthlyRecords[index]),
              ),
      ),
    );
  }
}

class _AttendanceTile extends StatelessWidget {
  final Map<String, dynamic> record;
  const _AttendanceTile({required this.record});

  @override
  Widget build(BuildContext context) {
    final date = DateTime.tryParse(record['date']?.toString() ?? '');
    final status = record['status']?.toString().replaceAll('_', ' ') ?? 'not marked';
    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: AppTheme.primaryLight,
          child: Icon(Icons.calendar_today_outlined, color: AppTheme.primary, size: 18),
        ),
        title: Text(date == null ? 'Attendance' : DateFormat('EEE, dd MMM yyyy').format(date)),
        subtitle: Text('${record['clock_in'] ?? '--:--'}  -  ${record['clock_out'] ?? '--:--'}'),
        trailing: Text(status, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
      ),
    );
  }
}

class _EmptyAttendance extends StatelessWidget {
  @override
  Widget build(BuildContext context) => const Center(
        child: Column(children: [
          Icon(Icons.fingerprint_rounded, size: 48, color: AppTheme.textMuted),
          SizedBox(height: 12),
          Text('No attendance records for this month', style: TextStyle(color: AppTheme.textSecondary)),
        ]),
      );
}
