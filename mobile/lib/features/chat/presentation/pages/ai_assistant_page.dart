import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';
import '../../../../app/di/dependencies.dart';
import '../../../../app/theme/app_colors.dart';
import '../bloc/chat_bloc.dart';
import '../../domain/entities/chat_message.dart';
import '../../../../core/widgets/status_badge/status_badge.dart';

class AiAssistantPage extends StatelessWidget {
  const AiAssistantPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) => ChatBloc(Dependencies.chatRepository, Dependencies.apiClient),
      child: const _AiAssistantView(),
    );
  }
}

class _AiAssistantView extends StatefulWidget {
  const _AiAssistantView();

  @override
  State<_AiAssistantView> createState() => _AiAssistantViewState();
}

class _AiAssistantViewState extends State<_AiAssistantView> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  void _send() {
    if (_controller.text.trim().isNotEmpty) {
      context.read<ChatBloc>().add(SendMessage(_controller.text));
      _controller.clear();
      Future.delayed(const Duration(milliseconds: 100), () {
        if (_scrollController.hasClients) {
          _scrollController.animateTo(
            _scrollController.position.maxScrollExtent,
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeOut,
          );
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('AI Assistant')),
      body: Column(
        children: [
          Expanded(
            child: BlocBuilder<ChatBloc, ChatState>(
              builder: (context, state) {
                if (state.messages.isEmpty) {
                  return const Center(child: Text('How can I help you today?', style: TextStyle(color: AppColors.textSecondary)));
                }
                return ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: state.messages.length,
                  itemBuilder: (context, index) {
                    final msg = state.messages[index];
                    return _MessageBubble(message: msg);
                  },
                );
              },
            ),
          ),
          BlocBuilder<ChatBloc, ChatState>(
            builder: (context, state) {
              if (state.error != null) {
                 return Container(
                   padding: const EdgeInsets.all(8),
                   color: AppColors.criticalBg,
                   child: Row(
                     children: [
                       const Icon(LucideIcons.alertCircle, color: AppColors.criticalText),
                       const SizedBox(width: 8),
                       Expanded(child: Text(state.error!, style: const TextStyle(color: AppColors.criticalText))),
                     ],
                   ),
                 );
              }
              if (state.isLoading) {
                return const Padding(
                  padding: EdgeInsets.all(8.0),
                  child: LinearProgressIndicator(color: AppColors.primary, backgroundColor: AppColors.surfaceElevated),
                );
              }
              return const SizedBox();
            },
          ),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: const BoxDecoration(
              color: AppColors.surface,
              border: Border(top: BorderSide(color: AppColors.border)),
            ),
            child: SafeArea(
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      decoration: InputDecoration(
                        hintText: 'Type your message...',
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide.none),
                        filled: true,
                        fillColor: AppColors.background,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      ),
                      onSubmitted: (_) => _send(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  CircleAvatar(
                    backgroundColor: AppColors.primary,
                    child: IconButton(
                      icon: const Icon(LucideIcons.send, color: Colors.white, size: 18),
                      onPressed: _send,
                    ),
                  )
                ],
              ),
            ),
          )
        ],
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  final ChatMessage message;
  const _MessageBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    if (message.role == MessageRole.progress) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 16),
        child: Row(
          children: [
            const SizedBox(width: 12, height: 12, child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary)),
            const SizedBox(width: 8),
            Text(message.text, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12, fontStyle: FontStyle.italic)),
          ],
        ),
      );
    }

    if (message.role == MessageRole.system && message.payload != null) {
       return _buildSystemCard(context);
    }

    final isUser = message.role == MessageRole.user;
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 8),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
        decoration: BoxDecoration(
          color: isUser ? AppColors.primary : AppColors.surfaceElevated,
          borderRadius: BorderRadius.circular(16).copyWith(
            bottomRight: isUser ? const Radius.circular(0) : const Radius.circular(16),
            bottomLeft: isUser ? const Radius.circular(16) : const Radius.circular(0),
          ),
        ),
        child: Text(
          message.text,
          style: TextStyle(color: isUser ? Colors.white : AppColors.textPrimary),
        ),
      ),
    );
  }

  Widget _buildSystemCard(BuildContext context) {
     final type = message.payload['type'];
     if (type == 'waiting_for_human') {
       return Card(
         color: AppColors.warningBg,
         margin: const EdgeInsets.symmetric(vertical: 8),
         child: Padding(
           padding: const EdgeInsets.all(12),
           child: Row(
             children: [
               const Icon(LucideIcons.userX, color: AppColors.warningText),
               const SizedBox(width: 8),
               Expanded(child: Text(message.text, style: const TextStyle(color: AppColors.warningText))),
             ],
           ),
         ),
       );
     }
     
     if (type == 'fraud_assessment') {
       Map<String, dynamic> data;
       try {
         data = jsonDecode(message.payload['data']);
       } catch (_) {
         return const SizedBox();
       }
       return Card(
         color: AppColors.criticalBg.withValues(alpha: 0.5),
         margin: const EdgeInsets.symmetric(vertical: 8),
         child: Padding(
           padding: const EdgeInsets.all(12),
           child: Column(
             crossAxisAlignment: CrossAxisAlignment.start,
             children: [
               Row(
                 children: [
                   const Icon(LucideIcons.alertTriangle, color: AppColors.criticalText, size: 16),
                   const SizedBox(width: 8),
                   const Text('Fraud Assessment', style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.criticalText)),
                   const Spacer(),
                   StatusBadge.critical(data['severity']?.toString() ?? 'HIGH'),
                 ],
               ),
               const SizedBox(height: 8),
               Text('Risk Score: ${data['risk_score']}', style: const TextStyle(color: Colors.white70)),
             ],
           ),
         ),
       );
     }
     return const SizedBox();
  }
}
