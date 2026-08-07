import 'package:flutter/material.dart';
import '../../domain/entities/fraud_alert.dart';
import '../../../../app/theme/app_colors.dart';
import '../../../../core/widgets/status_badge/status_badge.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

class FraudAlertCard extends StatelessWidget {
  final FraudAlertEntity alert;
  const FraudAlertCard({super.key, required this.alert});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(LucideIcons.alertOctagon, color: AppColors.critical, size: 20),
                const SizedBox(width: 8),
                const Expanded(child: Text('Security Alert', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white))),
                StatusBadge.critical(alert.severity),
              ],
            ),
            const SizedBox(height: 12),
            Text('Risk Score: ${alert.riskScore}/100', style: const TextStyle(color: AppColors.textSecondary, fontSize: 14)),
            const SizedBox(height: 8),
            if (alert.reasons.isNotEmpty) ...[
              Text(alert.reasons.first, style: const TextStyle(color: AppColors.textPrimary, fontSize: 14)),
            ]
          ],
        ),
      ),
    );
  }
}
