import 'package:flutter/material.dart';
import '../../../../app/theme/app_colors.dart';

class StatusBadge extends StatelessWidget {
  final String text;
  final Color bgColor;
  final Color textColor;

  const StatusBadge({
    super.key,
    required this.text,
    required this.bgColor,
    required this.textColor,
  });

  factory StatusBadge.success(String text) => StatusBadge(
    text: text,
    bgColor: AppColors.successBg,
    textColor: AppColors.successText,
  );
  factory StatusBadge.warning(String text) => StatusBadge(
    text: text,
    bgColor: AppColors.warningBg,
    textColor: AppColors.warningText,
  );
  factory StatusBadge.critical(String text) => StatusBadge(
    text: text,
    bgColor: AppColors.criticalBg,
    textColor: AppColors.criticalText,
  );
  factory StatusBadge.neutral(String text) => StatusBadge(
    text: text,
    bgColor: AppColors.border,
    textColor: AppColors.textPrimary,
  );

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        text.toUpperCase(),
        style: TextStyle(
          color: textColor,
          fontSize: 10,
          fontWeight: FontWeight.bold,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}
