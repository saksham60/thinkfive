import 'package:flutter/material.dart';
import 'package:mobile/app/theme/app_colors.dart';
import 'package:mobile/features/dashboard/domain/entities/customer_dashboard.dart';
import 'package:intl/intl.dart';

class AccountSummaryCard extends StatelessWidget {
  final AccountSummary summary;
  const AccountSummaryCard({super.key, required this.summary});

  @override
  Widget build(BuildContext context) {
    CurrencyTotal? displayTotal;
    if (summary.totalsByCurrency.isNotEmpty) {
      displayTotal = summary.totalsByCurrency.firstWhere(
        (t) => t.currency.toUpperCase() == 'USD',
        orElse: () => summary.totalsByCurrency.first,
      );
    }

    if (displayTotal == null) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(20),
          child: Text(
            'No account balances available.',
            style: TextStyle(color: AppColors.textSecondary),
          ),
        ),
      );
    }

    final formatCurrency = NumberFormat.simpleCurrency(name: displayTotal.currency);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Available Balance',
                  style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 14,
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.successBg.withValues(alpha: 0.5),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    '${summary.accountCount} ACTIVE',
                    style: const TextStyle(
                      color: AppColors.successText,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              formatCurrency.format(displayTotal.availableBalance),
              style: const TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              'Current: ${formatCurrency.format(displayTotal.currentBalance)}',
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 12,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
