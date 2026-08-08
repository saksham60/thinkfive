import 'package:flutter/material.dart';
import '../../domain/entities/transaction.dart';

class TransactionDetailPage extends StatelessWidget {
  final TransactionEntity transaction;

  const TransactionDetailPage({super.key, required this.transaction});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Transaction Detail')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            'ID: ${transaction.id}',
            style: Theme.of(context).textTheme.titleSmall,
          ),
          const SizedBox(height: 16),
          Text(
            transaction.merchant,
            style: Theme.of(context).textTheme.headlineMedium,
          ),
          const SizedBox(height: 8),
          Text(
            '${transaction.currency} ${transaction.amount.toStringAsFixed(2)}',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              color: transaction.hasFraudRisk == true
                  ? Colors.red
                  : Colors.green,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            'Status: ${transaction.status}',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          Text('Date: ${transaction.timestamp.toString()}'),
          if (transaction.category != null) ...[
            const SizedBox(height: 8),
            Text('Category: ${transaction.category}'),
          ],
          if (transaction.hasFraudRisk == true) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              color: Colors.red.withAlpha(26), // Approx 10% opacity
              child: const Row(
                children: [
                  Icon(Icons.warning, color: Colors.red),
                  SizedBox(width: 8),
                  Text(
                    'High Fraud Risk Detected',
                    style: TextStyle(
                      color: Colors.red,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}
