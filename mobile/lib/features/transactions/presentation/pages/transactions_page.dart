import 'package:flutter/material.dart';
import '../../domain/entities/transaction.dart';
import '../widgets/transaction_card/transaction_card.dart';
import 'package:go_router/go_router.dart';

class TransactionsPage extends StatelessWidget {
  final List<TransactionEntity> transactions;

  const TransactionsPage({super.key, required this.transactions});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Transactions')),
      body: transactions.isEmpty
          ? const Center(child: Text('No transactions found'))
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: transactions.length,
              itemBuilder: (context, i) {
                final t = transactions[i];
                return Padding(
                  padding: const EdgeInsets.only(bottom: 8.0),
                  child: InkWell(
                    onTap: () =>
                        context.push('/transactions/${t.id}', extra: t),
                    child: TransactionCard(transaction: t),
                  ),
                );
              },
            ),
    );
  }
}
