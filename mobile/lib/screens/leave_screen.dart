import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../services/leave_service.dart';
import '../utils/app_theme.dart';

class LeaveScreen extends StatefulWidget {
  const LeaveScreen({super.key});

  @override
  State<LeaveScreen> createState() => _LeaveScreenState();
}

class _LeaveScreenState extends State<LeaveScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => context.read<LeaveService>().load());
  }

  @override
  Widget build(BuildContext context) {
    final service = context.watch<LeaveService>();
    return Scaffold(
      appBar: AppBar(
        title: const Text('Leave Management'),
        actions: [IconButton(onPressed: () => _showApplyForm(context), icon: const Icon(Icons.add_rounded))],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: service.types.isEmpty ? null : () => _showApplyForm(context),
        icon: const Icon(Icons.edit_calendar_outlined),
        label: const Text('Apply leave'),
      ),
      body: RefreshIndicator(
        onRefresh: service.load,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 100),
          children: [
            _BalancesSection(balances: service.balances),
            const SizedBox(height: 20),
            const Text('My applications', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 10),
            if (service.applications.isEmpty) const _Message(text: 'No leave applications yet.'),
            ...service.applications.map((application) => _ApplicationTile(application: application)),
            const SizedBox(height: 20),
            const Text('Holiday calendar', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 10),
            if (service.holidays.isEmpty) const _Message(text: 'No holidays published for this year.'),
            ...service.holidays.map((holiday) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.event_available_outlined, color: AppTheme.secondary),
                  title: Text(holiday['name']?.toString() ?? 'Holiday'),
                  subtitle: Text(holiday['description']?.toString() ?? holiday['holiday_type']?.toString() ?? ''),
                  trailing: Text(_formatDate(holiday['date']?.toString())),
                )),
          ],
        ),
      ),
    );
  }

  Future<void> _showApplyForm(BuildContext context) async {
    final service = context.read<LeaveService>();
    final result = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      builder: (_) => _ApplyLeaveSheet(service: service),
    );
    if (result == true && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Leave application submitted')));
    }
  }
}

class _BalancesSection extends StatelessWidget {
  final List<Map<String, dynamic>> balances;
  const _BalancesSection({required this.balances});

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Available balance', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
            const SizedBox(height: 10),
            if (balances.isEmpty) const Text('Balances will appear after HR sets them up.'),
            ...balances.map((balance) {
              final type = Map<String, dynamic>.from(balance['leave_type'] ?? {});
              return ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(type['name']?.toString() ?? 'Leave'),
                trailing: Text('${balance['available_days'] ?? 0} days', style: const TextStyle(fontWeight: FontWeight.w700, color: AppTheme.primary)),
              );
            }),
          ]),
        ),
      );
}

class _ApplicationTile extends StatelessWidget {
  final Map<String, dynamic> application;
  const _ApplicationTile({required this.application});

  @override
  Widget build(BuildContext context) {
    final type = Map<String, dynamic>.from(application['leave_type'] ?? {});
    final status = application['status']?.toString() ?? 'pending';
    return Card(
      child: ListTile(
        title: Text(type['name']?.toString() ?? 'Leave'),
        subtitle: Text('${_formatDate(application['from_date']?.toString())} - ${_formatDate(application['to_date']?.toString())}\n${application['reason'] ?? ''}'),
        isThreeLine: true,
        trailing: Text(status.toUpperCase(), style: TextStyle(fontSize: 11, color: status == 'approved' ? AppTheme.secondary : AppTheme.accent, fontWeight: FontWeight.w700)),
      ),
    );
  }
}

class _ApplyLeaveSheet extends StatefulWidget {
  final LeaveService service;
  const _ApplyLeaveSheet({required this.service});

  @override
  State<_ApplyLeaveSheet> createState() => _ApplyLeaveSheetState();
}

class _ApplyLeaveSheetState extends State<_ApplyLeaveSheet> {
  String? _typeId;
  DateTime _from = DateTime.now();
  DateTime _to = DateTime.now();
  final _reason = TextEditingController();

  @override
  void dispose() { _reason.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) => Padding(
        padding: EdgeInsets.fromLTRB(16, 20, 16, MediaQuery.viewInsetsOf(context).bottom + 20),
        child: SingleChildScrollView(child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
          const Text('Apply for leave', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            value: _typeId,
            decoration: const InputDecoration(labelText: 'Leave type'),
            items: widget.service.types.map((type) => DropdownMenuItem(value: type['id'].toString(), child: Text(type['name'].toString()))).toList(),
            onChanged: (value) => setState(() => _typeId = value),
          ),
          const SizedBox(height: 12),
          Row(children: [Expanded(child: _dateButton('From', _from, (date) => setState(() => _from = date))), const SizedBox(width: 10), Expanded(child: _dateButton('To', _to, (date) => setState(() => _to = date)))]),
          const SizedBox(height: 12),
          TextField(controller: _reason, maxLines: 3, decoration: const InputDecoration(labelText: 'Reason', alignLabelWithHint: true)),
          const SizedBox(height: 16),
          SizedBox(width: double.infinity, child: ElevatedButton(onPressed: widget.service.isLoading ? null : _submit, child: const Text('Submit application'))),
        ])),
      );

  Widget _dateButton(String label, DateTime value, ValueChanged<DateTime> onChanged) => OutlinedButton.icon(
        onPressed: () async {
          final date = await showDatePicker(context: context, firstDate: DateTime.now().subtract(const Duration(days: 365)), lastDate: DateTime.now().add(const Duration(days: 365)), initialDate: value);
          if (date != null) onChanged(date);
        },
        icon: const Icon(Icons.calendar_today_outlined, size: 16),
        label: Text('$label\n${DateFormat('dd MMM yyyy').format(value)}', textAlign: TextAlign.left),
      );

  Future<void> _submit() async {
    if (_typeId == null || _reason.text.trim().isEmpty || _from.isAfter(_to)) return;
    final success = await widget.service.applyLeave(leaveTypeId: _typeId!, fromDate: _from, toDate: _to, reason: _reason.text);
    if (mounted && success) Navigator.pop(context, true);
  }
}

class _Message extends StatelessWidget {
  final String text;
  const _Message({required this.text});
  @override
  Widget build(BuildContext context) => Padding(padding: const EdgeInsets.symmetric(vertical: 12), child: Text(text, style: const TextStyle(color: AppTheme.textSecondary)));
}

String _formatDate(String? value) {
  final date = value == null ? null : DateTime.tryParse(value);
  return date == null ? '--' : DateFormat('dd MMM yyyy').format(date);
}
