import 'package:flutter/material.dart';
import '../../domain/entities/case_entity.dart';
import '../../../../app/theme/app_colors.dart';
import '../../../../core/widgets/status_badge/status_badge.dart';

class CaseStatusCard extends StatelessWidget {
  final CaseEntity caseEntity;
  const CaseStatusCard({super.key, required this.caseEntity});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Case #${caseEntity.id.split('-').first}', style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
                const SizedBox(height: 4),
                Text(caseEntity.type, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
              ],
            ),
            if (caseEntity.status == 'WAITING_FOR_HUMAN')
              StatusBadge.warning('Review Pending')
            else if (caseEntity.status == 'OPEN' || caseEntity.status == 'INVESTIGATING')
              StatusBadge.neutral(caseEntity.status)
            else
              StatusBadge.success(caseEntity.status),
          ],
        ),
      ),
    );
  }
}
