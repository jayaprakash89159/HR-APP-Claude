import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/leave_service.dart';
import '../utils/app_theme.dart';

class LeaveBalanceCard extends StatelessWidget {
  const LeaveBalanceCard({super.key});

  @override
  Widget build(BuildContext context) {
    final service = context.watch<LeaveService>();
    if (service.balances.isEmpty && !service.isLoading) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (context.mounted && service.balances.isEmpty && !service.isLoading) service.load();
      });
    }
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Leave balance', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
          const SizedBox(height: 12),
          if (service.isLoading && service.balances.isEmpty)
            const LinearProgressIndicator()
          else if (service.balances.isEmpty)
            const Text('No leave balances available', style: TextStyle(color: AppTheme.textSecondary))
          else
            ...service.balances.take(3).map((balance) {
              final type = Map<String, dynamic>.from(balance['leave_type'] ?? {});
              return ListTile(
                contentPadding: EdgeInsets.zero,
                leading: CircleAvatar(
                  backgroundColor: AppTheme.primaryLight,
                  child: Text('${balance['available_days'] ?? 0}', style: const TextStyle(color: AppTheme.primary, fontWeight: FontWeight.w700)),
                ),
                title: Text(type['name']?.toString() ?? 'Leave'),
                subtitle: const Text('days available'),
              );
            }),
        ]),
      ),
    );
  }
}