import 'package:flutter/material.dart';
import '../../../../app/theme/app_colors.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

class AppError extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;
  
  const AppError({super.key, required this.message, this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(LucideIcons.alertTriangle, color: AppColors.critical, size: 48),
            const SizedBox(height: 16),
            Text(message, textAlign: TextAlign.center, style: const TextStyle(color: AppColors.textPrimary)),
            if (onRetry != null) ...[
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: onRetry,
                icon: const Icon(LucideIcons.refreshCw, size: 16),
                label: const Text('Retry'),
              )
            ]
          ],
        ),
      ),
    );
  }
}
