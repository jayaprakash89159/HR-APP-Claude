import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../services/payslip_service.dart';
import '../utils/app_theme.dart';

class PayslipScreen extends StatefulWidget {
  const PayslipScreen({super.key});

  @override
  State<PayslipScreen> createState() => _PayslipScreenState();
}

class _PayslipScreenState extends State<PayslipScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => context.read<PayslipService>().load());
  }

  @override
  Widget build(BuildContext context) {
    final service = context.watch<PayslipService>();
    return Scaffold(
      appBar: AppBar(title: const Text('My Payslips')),
      body: RefreshIndicator(
        onRefresh: service.load,
        child: service.isLoading && service.payslips.isEmpty
            ? const Center(child: CircularProgressIndicator())
            : service.payslips.isEmpty
                ? ListView(children: const [SizedBox(height: 220), Center(child: Text('No released payslips available'))])
                : ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: service.payslips.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 10),
                    itemBuilder: (_, index) => _PayslipTile(payslip: service.payslips[index]),
                  ),
      ),
    );
  }
}

class _PayslipTile extends StatelessWidget {
  final Map<String, dynamic> payslip;
  const _PayslipTile({required this.payslip});

  @override
  Widget build(BuildContext context) {
    final period = Map<String, dynamic>.from(payslip['period'] ?? {});
    final month = period['month_name']?.toString() ?? '${period['year']}-${period['month']}';
    final status = payslip['status']?.toString() ?? 'released';
    return Card(
      child: ListTile(
        leading: const CircleAvatar(
          backgroundColor: AppTheme.primaryLight,
          child: Icon(Icons.receipt_long_outlined, color: AppTheme.primary),
        ),
        title: Text(month),
        subtitle: Text('${payslip['payslip_number'] ?? ''}\n${status.toUpperCase()}'),
        isThreeLine: true,
        trailing: Text(
          '₹${NumberFormat('#,##0.00').format(payslip['net_salary'] ?? 0)}',
          style: const TextStyle(fontWeight: FontWeight.w700, color: AppTheme.secondary),
        ),
        onTap: () => _showDetail(context, payslip['id'].toString()),
      ),
    );
  }

  Future<void> _showDetail(BuildContext context, String id) async {
    final service = context.read<PayslipService>();
    await service.loadDetail(id);
    if (!context.mounted || service.selected == null) return;
    final detail = service.selected!;
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (_) => _PayslipDetail(detail: detail),
    );
  }
}

class _PayslipDetail extends StatelessWidget {
  final Map<String, dynamic> detail;
  const _PayslipDetail({required this.detail});

  @override
  Widget build(BuildContext context) {
    final period = Map<String, dynamic>.from(detail['period'] ?? {});
    final rows = <String, dynamic>{
      'Basic': detail['basic'],
      'HRA': detail['hra'],
      'Special allowance': detail['special_allowance'],
      'Gross earnings': detail['gross_earnings'],
      'PF': detail['pf_employee'],
      'ESI': detail['esi_employee'],
      'Professional tax': detail['professional_tax'],
      'TDS': detail['tds'],
      'Total deductions': detail['total_deductions'],
      'Net salary': detail['net_salary'],
    };
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: SingleChildScrollView(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Payslip ${period['year']}-${period['month']}', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
            const SizedBox(height: 16),
            Text('Attendance: ${detail['days_present'] ?? 0} present, ${detail['days_absent'] ?? 0} absent'),
            const Divider(height: 28),
            ...rows.entries.map((row) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 6),
                  child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                    Text(row.key),
                    Text('₹${NumberFormat('#,##0.00').format(row.value ?? 0)}', style: const TextStyle(fontWeight: FontWeight.w600)),
                  ]),
                )),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () async {
                  final opened = await context.read<PayslipService>().openPdf(detail['id'].toString());
                  if (context.mounted && !opened) {
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('PDF is not available on this platform or has not been released.')));
                  }
                },
                icon: const Icon(Icons.picture_as_pdf_outlined),
                label: const Text('Open PDF payslip'),
              ),
            ),
          ]),
        ),
      ),
    );
  }
}
