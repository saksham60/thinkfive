import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../domain/repositories/chat_repository.dart';
import '../../../../core/sse/sse_client_factory.dart';
import '../../../../core/sse/i_sse_client.dart';
import '../../../../core/network/api_client.dart';
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
  final String eventType;
  final String data;
  _SseEventReceived(this.eventType, this.data);
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
    on<_SseError>((event, emit) => emit(state.copyWith(error: 'Connection error')));
  }

  Future<void> _onSendMessage(SendMessage event, Emitter<ChatState> emit) async {
    final userMsg = ChatMessage(id: DateTime.now().toString(), text: event.text, role: MessageRole.user);
    final messages = List<ChatMessage>.from(state.messages)..add(userMsg);
    // clear error on new message
    emit(ChatState(
      messages: messages,
      isLoading: true,
      conversationId: state.conversationId,
    ));

    try {
      final convId = await _repository.submitMessage(event.text, conversationId: state.conversationId);
      if (convId != state.conversationId) {
        emit(state.copyWith(conversationId: convId));
        _connectSse(convId);
      }
    } catch (e) {
      emit(state.copyWith(isLoading: false, error: 'Failed to send message'));
    }
  }

  void _connectSse(String conversationId) {
    _sseSubscription?.cancel();
    _sseClient?.close();

    _sseClient = SseClientFactory.create(_apiClient, conversationId);
    _sseSubscription = _sseClient!.stream.listen(
      (event) {
        if (event.event != null) {
          add(_SseEventReceived(event.event!, event.data));
        }
      },
      onError: (err) {
        add(_SseError());
      }
    );
  }

  void _onSseEventReceived(_SseEventReceived event, Emitter<ChatState> emit) {
    final messages = List<ChatMessage>.from(state.messages);
    
    if (event.eventType == 'agent_started' || event.eventType == 'tool_call') {
      messages.add(ChatMessage(
        id: DateTime.now().toString(),
        text: event.data,
        role: MessageRole.progress,
      ));
    } else if (event.eventType == 'final_response' || event.eventType == 'message') {
      messages.add(ChatMessage(
        id: DateTime.now().toString(),
        text: event.data,
        role: MessageRole.ai,
      ));
    } else if (event.eventType == 'fraud_assessment') {
      messages.add(ChatMessage(
        id: DateTime.now().toString(),
        text: 'Fraud Assessment',
        role: MessageRole.system,
        payload: {'type': 'fraud_assessment', 'data': event.data},
      ));
    } else if (event.eventType == 'case_created') {
       messages.add(ChatMessage(
        id: DateTime.now().toString(),
        text: 'Case Created',
        role: MessageRole.system,
        payload: {'type': 'case_created', 'data': event.data},
      ));
    } else if (event.eventType == 'waiting_for_human') {
      messages.add(ChatMessage(
        id: DateTime.now().toString(),
        text: event.data,
        role: MessageRole.system,
        payload: {'type': 'waiting_for_human'},
      ));
    } else if (event.eventType == 'approval_result') {
      messages.add(ChatMessage(
        id: DateTime.now().toString(),
        text: 'Action ${event.data}',
        role: MessageRole.system,
      ));
    }

    emit(state.copyWith(messages: messages, isLoading: false));
  }

  @override
  Future<void> close() {
    _sseSubscription?.cancel();
    _sseClient?.close();
    return super.close();
  }
}
