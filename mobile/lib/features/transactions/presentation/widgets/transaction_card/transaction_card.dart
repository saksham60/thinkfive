import 'package:flutter/material.dart';
import 'package:mobile/features/transactions/domain/entities/transaction.dart';
import 'package:mobile/app/theme/app_colors.dart';
import 'package:intl/intl.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

class TransactionCard extends StatelessWidget {
  final TransactionEntity transaction;
  const TransactionCard({super.key, required this.transaction});

  @override
  Widget build(BuildContext context) {
    final formatCurrency = NumberFormat.simpleCurrency(name: transaction.currency);
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      tileColor: AppColors.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: AppColors.border),
      ),
      leading: Container(
        width: 40, height: 40,
        decoration: BoxDecoration(color: AppColors.surfaceElevated, borderRadius: BorderRadius.circular(8)),
        child: const Icon(LucideIcons.store, color: AppColors.primary),
      ),
      title: Text(transaction.merchant, style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
      subtitle: Text(DateFormat('MMM dd, yyyy').format(transaction.timestamp), style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
      trailing: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Text(formatCurrency.format(transaction.amount), style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
          if (transaction.hasFraudRisk == true)
            const Text('Review', style: TextStyle(color: AppColors.critical, fontSize: 10, fontWeight: FontWeight.bold))
          else 
            Text(transaction.status, style: const TextStyle(color: AppColors.textSecondary, fontSize: 10)),
        ],
      ),
    );
  }
}
