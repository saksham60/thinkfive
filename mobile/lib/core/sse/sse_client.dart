import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import '../network/api_client.dart';
import 'sse_event.dart';
import 'sse_parser.dart';
import 'i_sse_client.dart';

class SseClient implements ISseClient {
  final ApiClient _apiClient;
  final String _url;
  
  StreamController<SseEvent>? _controller;
  CancelToken? _cancelToken;
  
  String? _lastEventId;
  int _reconnectDelayMs = 1000;
  static const int _maxReconnectDelayMs = 15000;
  bool _isClosed = false;

  SseClient(this._apiClient, this._url);

  Stream<SseEvent> get stream {
    if (_controller == null || _controller!.isClosed) {
      _controller = StreamController<SseEvent>.broadcast(
        onListen: _connect,
        onCancel: close,
      );
    }
    return _controller!.stream;
  }

  Future<void> _connect() async {
    if (_isClosed) return;

    _cancelToken = CancelToken();
    final parser = SseParser();

    try {
      final headers = {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache',
      };
      
      if (_lastEventId != null) {
        headers['Last-Event-ID'] = _lastEventId!;
      }

      final response = await _apiClient.dio.get<ResponseBody>(
        _url,
        options: Options(
          headers: headers,
          responseType: ResponseType.stream,
          // Do not retry implicitly if 401
          validateStatus: (status) => status != null && status < 500,
        ),
        cancelToken: _cancelToken,
      );

      if (response.statusCode == 401 || response.statusCode == 403) {
        _controller?.addError(DioException(
          requestOptions: response.requestOptions,
          response: Response(
            requestOptions: response.requestOptions,
            statusCode: response.statusCode,
          ),
          type: DioExceptionType.badResponse,
        ));
        close();
        return;
      }

      // Reset delay on successful connection
      _reconnectDelayMs = 1000;

      final stream = response.data!.stream;
      await for (final Uint8List chunk in stream) {
        if (_isClosed) break;
        final stringChunk = utf8.decode(chunk, allowMalformed: true);
        final events = parser.parseChunk(stringChunk);
        
        for (final event in events) {
          if (event.id != null) {
            _lastEventId = event.id;
          }
          if (event.retry != null) {
             // We could update _reconnectDelayMs here if we wanted to respect the server's retry
          }
          if (!_isClosed && _controller != null && !_controller!.isClosed) {
            _controller?.add(event);
          }
        }
      }
    } catch (e) {
      if (e is DioException && e.type == DioExceptionType.cancel) {
        // Deliberately closed
        return;
      }
      
      if (!_isClosed && _controller != null && !_controller!.isClosed) {
        // Pass error but reconnect
        // _controller?.addError(e); 
      }
    }

    if (!_isClosed) {
      _scheduleReconnect();
    }
  }

  void _scheduleReconnect() {
    if (_isClosed) return;
    
    Future.delayed(Duration(milliseconds: _reconnectDelayMs), () {
      if (!_isClosed) {
        _reconnectDelayMs = (_reconnectDelayMs * 2).clamp(1000, _maxReconnectDelayMs);
        _connect();
      }
    });
  }

  void close() {
    _isClosed = true;
    _cancelToken?.cancel('SSE Client Closed');
    _controller?.close();
  }
}
