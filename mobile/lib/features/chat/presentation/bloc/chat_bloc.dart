import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../domain/repositories/chat_repository.dart';
import '../../../../core/sse/sse_client_factory.dart';
import '../../../../core/sse/i_sse_client.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/sse/app_sse_event.dart';
import '../../domain/entities/chat_message.dart';

abstract class ChatEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class SendMessage extends ChatEvent {
  final String text;
  SendMessage(this.text);
  @override
  List<Object?> get props => [text];
}

class _SseEventReceived extends ChatEvent {
  final AppSseEvent sseEvent;
  _SseEventReceived(this.sseEvent);
}

class _SseError extends ChatEvent {}

class ChatState extends Equatable {
  final List<ChatMessage> messages;
  final bool isLoading;
  final String? conversationId;
  final String? error;

  const ChatState({
    this.messages = const [],
    this.isLoading = false,
    this.conversationId,
    this.error,
  });

  ChatState copyWith({
    List<ChatMessage>? messages,
    bool? isLoading,
    String? conversationId,
    String? error,
  }) {
    return ChatState(
      messages: messages ?? this.messages,
      isLoading: isLoading ?? this.isLoading,
      conversationId: conversationId ?? this.conversationId,
      error: error,
    );
  }

  @override
  List<Object?> get props => [messages, isLoading, conversationId, error];
}

class ChatBloc extends Bloc<ChatEvent, ChatState> {
  final ChatRepository _repository;
  final ApiClient _apiClient;
  ISseClient? _sseClient;
  StreamSubscription? _sseSubscription;

  ChatBloc(this._repository, this._apiClient) : super(const ChatState()) {
    on<SendMessage>(_onSendMessage);
    on<_SseEventReceived>(_onSseEventReceived);
    on<_SseError>(
      (event, emit) => emit(state.copyWith(error: 'Connection error')),
    );
  }

  Future<void> _onSendMessage(
    SendMessage event,
    Emitter<ChatState> emit,
  ) async {
    final userMsg = ChatMessage(
      id: DateTime.now().toString(),
      text: event.text,
      role: MessageRole.user,
    );
    final messages = List<ChatMessage>.from(state.messages)..add(userMsg);
    // clear error on new message
    emit(
      ChatState(
        messages: messages,
        isLoading: true,
        conversationId: state.conversationId,
      ),
    );

    try {
      final convId = await _repository.submitMessage(
        event.text,
        conversationId: state.conversationId,
      );
      if (convId != state.conversationId) {
        emit(state.copyWith(conversationId: convId));
        _connectSse(convId);
      }
    } catch (e) {
      String errMsg = 'Failed to send message';
      if (e.toString().contains('403') || e.toString().contains('RBAC')) {
        errMsg =
            'Access Denied: You do not have permission to use the AI assistant.';
      }
      emit(state.copyWith(isLoading: false, error: errMsg));
    }
  }

  void _connectSse(String conversationId) {
    _sseSubscription?.cancel();
    _sseClient?.close();

    _sseClient = SseClientFactory.create(_apiClient, conversationId);
    _sseSubscription = _sseClient!.stream.listen(
      (event) {
        add(_SseEventReceived(event));
      },
      onError: (err) {
        add(_SseError());
      },
    );
  }

  void _onSseEventReceived(_SseEventReceived event, Emitter<ChatState> emit) {
    final messages = List<ChatMessage>.from(state.messages);
    final sseEvent = event.sseEvent;

    if (sseEvent is AgentStartedEvent) {
      messages.add(
        ChatMessage(
          id: sseEvent.id,
          text: 'Agent started: ${sseEvent.agentName}',
          role: MessageRole.progress,
        ),
      );
    } else if (sseEvent is ToolStartedEvent) {
      messages.add(
        ChatMessage(
          id: sseEvent.id,
          text: 'Using tool: ${sseEvent.toolName}',
          role: MessageRole.progress,
        ),
      );
    } else if (sseEvent is ChatCompletedEvent) {
      messages.add(
        ChatMessage(
          id: sseEvent.id,
          text: sseEvent.response,
          role: MessageRole.ai,
        ),
      );
      emit(state.copyWith(messages: messages, isLoading: false));
      return;
    } else if (sseEvent is FraudAssessmentEvent) {
      messages.add(
        ChatMessage(
          id: sseEvent.id,
          text: 'Fraud Assessment',
          role: MessageRole.system,
          payload: {'type': 'fraud_assessment', 'data': sseEvent.data},
        ),
      );
    } else if (sseEvent is CaseCreatedEvent) {
      messages.add(
        ChatMessage(
          id: sseEvent.id,
          text: 'Case Created',
          role: MessageRole.system,
          payload: {'type': 'case_created', 'data': sseEvent.caseId},
        ),
      );
    } else if (sseEvent is WorkflowInterruptedEvent) {
      messages.add(
        ChatMessage(
          id: sseEvent.id,
          text: 'A human reviewer is required before this action can continue.',
          role: MessageRole.system,
          payload: {'type': 'waiting_for_human'},
        ),
      );
    } else if (sseEvent is ApprovalResultEvent) {
      messages.add(
        ChatMessage(
          id: sseEvent.id,
          text: 'Action ${sseEvent.result}',
          role: MessageRole.system,
        ),
      );
    } else if (sseEvent is ChatFailedEvent) {
      messages.add(
        ChatMessage(
          id: sseEvent.id,
          text: 'Error: ${sseEvent.error}',
          role: MessageRole.system,
        ),
      );
      emit(state.copyWith(messages: messages, isLoading: false));
      return;
    } else if (sseEvent is ApprovalRequestedEvent) {
      messages.add(
        ChatMessage(
          id: sseEvent.id,
          text: 'Approval Requested',
          role: MessageRole.system,
          payload: {
            'type': 'approval_requested',
            'approval_id': sseEvent.approvalId,
            'case_id': sseEvent.caseId,
          },
        ),
      );
    }

    emit(state.copyWith(messages: messages));
  }

  @override
  Future<void> close() {
    _sseSubscription?.cancel();
    _sseClient?.close();
    return super.close();
  }
}
