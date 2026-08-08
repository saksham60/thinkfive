import 'dart:async';
import 'dart:convert';
import 'package:flutter/widgets.dart';
import 'package:dio/dio.dart';
import '../network/api_client.dart';

import 'sse_parser.dart';
import 'i_sse_client.dart';
import 'sse_cursor_store.dart';
import 'app_sse_event.dart';
import 'sse_payload_decoder.dart';

class SseClient with WidgetsBindingObserver implements ISseClient {
  final ApiClient _apiClient;
  final String _url;
  final String _conversationId;
  final SseCursorStore _cursorStore = SseCursorStore();

  StreamController<AppSseEvent>? _controller;
  CancelToken? _cancelToken;

  int _reconnectDelayMs = 1000;
  static const int _maxReconnectDelayMs = 15000;
  bool _isClosed = false;
  bool _isInBackground = false;

  SseClient(this._apiClient, this._url, this._conversationId) {
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.hidden) {
      _isInBackground = true;
      _disconnect();
    } else if (state == AppLifecycleState.resumed) {
      _isInBackground = false;
      if (!_isClosed) {
        _connect();
      }
    }
  }

  @override
  Stream<AppSseEvent> get stream {
    if (_controller == null || _controller!.isClosed) {
      _controller = StreamController<AppSseEvent>.broadcast(
        onListen: () {
          if (!_isInBackground) _connect();
        },
        onCancel: close,
      );
    }
    return _controller!.stream;
  }

  void _disconnect() {
    _cancelToken?.cancel('Background or reconnect');
    _cancelToken = null;
  }

  Future<void> _connect() async {
    if (_isClosed || _isInBackground) return;

    _disconnect(); // ensure any previous is cancelled
    _cancelToken = CancelToken();
    final parser = SseParser();

    try {
      final headers = {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache',
      };

      String? lastEventId = await _cursorStore.getLastEventId(_conversationId);
      headers['Last-Event-ID'] = lastEventId ?? '-1';

      final response = await _apiClient.dio.get<ResponseBody>(
        _url,
        options: Options(
          headers: headers,
          responseType: ResponseType.stream,
          validateStatus: (status) => status != null && status < 500,
        ),
        cancelToken: _cancelToken,
      );

      if (response.statusCode == 401 || response.statusCode == 403) {
        _controller?.addError(
          DioException(
            requestOptions: response.requestOptions,
            response: Response(
              requestOptions: response.requestOptions,
              statusCode: response.statusCode,
            ),
            type: DioExceptionType.badResponse,
          ),
        );
        close();
        return;
      }

      _reconnectDelayMs = 1000;

      final stream = response.data!.stream;
      await for (final String stringChunk in stream.cast<List<int>>().transform(
        const Utf8Decoder(allowMalformed: true),
      )) {
        if (_isClosed || _cancelToken?.isCancelled == true) break;

        final events = parser.parseChunk(stringChunk);
        for (final rawEvent in events) {
          if (rawEvent.id != null) {
            await _cursorStore.saveLastEventId(_conversationId, rawEvent.id!);
          }
          if (!_isClosed && _controller != null && !_controller!.isClosed) {
            _controller?.add(SsePayloadDecoder.decode(rawEvent));
          }
        }
      }
    } catch (e) {
      if (e is DioException && e.type == DioExceptionType.cancel) {
        return;
      }
    }

    if (!_isClosed && !_isInBackground) {
      _scheduleReconnect();
    }
  }

  void _scheduleReconnect() {
    if (_isClosed || _isInBackground) return;

    Future.delayed(Duration(milliseconds: _reconnectDelayMs), () {
      if (!_isClosed && !_isInBackground) {
        _reconnectDelayMs = (_reconnectDelayMs * 2).clamp(
          1000,
          _maxReconnectDelayMs,
        );
        _connect();
      }
    });
  }

  @override
  void close() {
    _isClosed = true;
    WidgetsBinding.instance.removeObserver(this);
    _disconnect();
    _controller?.close();
  }
}
