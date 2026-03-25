import 'dart:async' show TimeoutException;
import 'dart:convert';
import 'dart:io' show Platform;

import 'package:http/http.dart' as http;

import 'tinyhumans_error.dart';
import 'types.dart';

class TinyHumansMemoryClient {
  static const _defaultBaseUrl = 'https://api.tinyhumans.ai';
  static const _defaultModelId = 'neocortex-mk1';

  final String _token;
  final String _baseUrl;
  final String _modelId;
  final http.Client _httpClient;
  final bool _ownsClient;

  TinyHumansMemoryClient(
    String token, {
    String? modelId,
    String? baseUrl,
    http.Client? httpClient,
  })  : _token = token,
        _modelId = (modelId != null && modelId.trim().isNotEmpty)
            ? modelId
            : _defaultModelId,
        _baseUrl = (baseUrl ??
                Platform.environment['TINYHUMANS_BASE_URL'] ??
                _defaultBaseUrl)
            .replaceAll(RegExp(r'/+$'), ''),
        _httpClient = httpClient ?? http.Client(),
        _ownsClient = httpClient == null {
    if (token.trim().isEmpty) {
      throw ArgumentError('token is required');
    }
  }

  Future<InsertMemoryResponse> insertMemory(InsertMemoryParams params) async {
    params.validate();
    final result = await _post('/memory/insert', params.toJson());
    return InsertMemoryResponse.fromJson(result);
  }

  Future<RecallMemoryResponse> recallMemory([RecallMemoryParams? params]) async {
    params ??= RecallMemoryParams();
    params.validate();
    final result = await _post('/memory/recall', params.toJson());
    return RecallMemoryResponse.fromJson(result);
  }

  Future<DeleteMemoryResponse> deleteMemory([DeleteMemoryParams? params]) async {
    params ??= DeleteMemoryParams();
    params.validate();
    final result = await _post('/memory/admin/delete', params.toJson());
    return DeleteMemoryResponse.fromJson(result);
  }

  Future<QueryMemoryResponse> queryMemory(QueryMemoryParams params) async {
    params.validate();
    final result = await _post('/memory/query', params.toJson());
    return QueryMemoryResponse.fromJson(result);
  }

  Future<RecallMemoriesResponse> recallMemories(
      [RecallMemoriesParams? params]) async {
    params ??= RecallMemoriesParams();
    params.validate();
    final result = await _post('/memory/memories/recall', params.toJson());
    return RecallMemoriesResponse.fromJson(result);
  }

  // ── Chat ──

  Future<Map<String, dynamic>> chatMemory(ChatMemoryParams params) async {
    params.validate();
    return await _post('/memory/chat', params.toJson());
  }

  Future<Map<String, dynamic>> chatMemoryContext(
      ChatMemoryParams params) async {
    params.validate();
    return await _post('/memory/conversations', params.toJson());
  }

  // ── Interactions ──

  Future<Map<String, dynamic>> interactMemory(
      InteractMemoryParams params) async {
    params.validate();
    return await _post('/memory/interact', params.toJson());
  }

  Future<Map<String, dynamic>> recordInteractions(
      InteractMemoryParams params) async {
    params.validate();
    return await _post('/memory/interactions', params.toJson());
  }

  // ── Advanced Recall ──

  Future<Map<String, dynamic>> recallThoughts(
      [RecallThoughtsParams? params]) async {
    params ??= RecallThoughtsParams();
    params.validate();
    return await _post('/memory/memories/thoughts', params.toJson());
  }

  Future<Map<String, dynamic>> queryMemoryContext(
      QueryMemoryContextParams params) async {
    params.validate();
    return await _post('/memory/queries', params.toJson());
  }

  // ── Documents ──

  Future<Map<String, dynamic>> insertDocument(
      InsertDocumentParams params) async {
    params.validate();
    return await _post('/memory/documents', params.toJson());
  }

  Future<Map<String, dynamic>> insertDocumentsBatch(
      InsertDocumentsBatchParams params) async {
    params.validate();
    return await _post('/memory/documents/batch', params.toJson());
  }

  Future<Map<String, dynamic>> listDocuments(
      [ListDocumentsParams? params]) async {
    params ??= ListDocumentsParams();
    return await _get('/memory/documents', params.toQueryParams());
  }

  Future<Map<String, dynamic>> getDocument(GetDocumentParams params) async {
    params.validate();
    return await _get(
      '/memory/documents/${Uri.encodeComponent(params.id)}',
      params.toQueryParams(),
    );
  }

  Future<Map<String, dynamic>> deleteDocument(String documentId,
      [String? namespace]) async {
    if (documentId.trim().isEmpty) {
      throw ArgumentError('documentId is required');
    }
    final queryParams = <String, String>{};
    if (namespace != null) queryParams['namespace'] = namespace;
    return await _delete(
      '/memory/documents/${Uri.encodeComponent(documentId)}',
      queryParams,
    );
  }

  // ── Admin & Utility ──

  Future<Map<String, dynamic>> getGraphSnapshot(
      [GraphSnapshotParams? params]) async {
    params ??= GraphSnapshotParams();
    return await _get('/memory/admin/graph-snapshot', params.toQueryParams());
  }

  Future<Map<String, dynamic>> getIngestionJob(String jobId) async {
    if (jobId.trim().isEmpty) {
      throw ArgumentError('jobId is required');
    }
    return await _get(
        '/memory/ingestion/jobs/${Uri.encodeComponent(jobId)}');
  }

  Future<Map<String, dynamic>> waitForIngestionJob(String jobId,
      [WaitForIngestionJobOptions? opts]) async {
    opts ??= WaitForIngestionJobOptions();
    for (var i = 0; i < opts.maxAttempts; i++) {
      final result = await getIngestionJob(jobId);
      final data = result['data'] as Map<String, dynamic>?;
      if (data != null) {
        final state = data['state'] as String?;
        if (state == 'completed' || state == 'failed') {
          return result;
        }
      }
      await Future.delayed(Duration(milliseconds: opts.intervalMs));
    }
    throw TimeoutException(
      'Ingestion job $jobId did not complete within ${opts.maxAttempts} attempts',
    );
  }

  /// Recall memory context. POST /memory/memories/context
  Future<Map<String, dynamic>> recallMemoriesContext({
    String? namespace,
    double? maxChunks,
  }) async {
    final body = <String, dynamic>{};
    if (namespace != null) body['namespace'] = namespace;
    if (maxChunks != null) body['maxChunks'] = maxChunks;
    return _post('/memory/memories/context', body);
  }

  /// Check memory server health. GET /memory/health
  Future<Map<String, dynamic>> memoryHealth() async {
    return _get('/memory/health');
  }

  /// Sync OpenClaw memory files to backend. POST /memory/sync
  Future<Map<String, dynamic>> syncMemory({
    required String workspaceId,
    required String agentId,
    required List<Map<String, String>> files,
    String? source,
  }) async {
    if (workspaceId.isEmpty) {
      throw ArgumentError('workspaceId is required');
    }
    if (agentId.isEmpty) {
      throw ArgumentError('agentId is required');
    }
    if (files.isEmpty) {
      throw ArgumentError('files is required and must be non-empty');
    }
    final body = <String, dynamic>{
      'workspaceId': workspaceId,
      'agentId': agentId,
      'files': files,
    };
    if (source != null) body['source'] = source;
    return _post('/memory/sync', body);
  }

  Future<Map<String, dynamic>> _post(
      String path, Map<String, dynamic> body) async {
    final url = Uri.parse('$_baseUrl$path');
    final response = await _httpClient.post(
      url,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $_token',
        'X-Model-Id': _modelId,
      },
      body: jsonEncode(body),
    );
    return _handleResponse(response);
  }

  Future<Map<String, dynamic>> _get(String path,
      [Map<String, String>? queryParams]) async {
    var uri = Uri.parse('$_baseUrl$path');
    if (queryParams != null && queryParams.isNotEmpty) {
      uri = uri.replace(queryParameters: queryParams);
    }
    final response = await _httpClient.get(
      uri,
      headers: {
        'Authorization': 'Bearer $_token',
        'X-Model-Id': _modelId,
      },
    );
    return _handleResponse(response);
  }

  Future<Map<String, dynamic>> _delete(String path,
      [Map<String, String>? queryParams]) async {
    var uri = Uri.parse('$_baseUrl$path');
    if (queryParams != null && queryParams.isNotEmpty) {
      uri = uri.replace(queryParameters: queryParams);
    }
    final response = await _httpClient.delete(
      uri,
      headers: {
        'Authorization': 'Bearer $_token',
        'X-Model-Id': _modelId,
      },
    );
    return _handleResponse(response);
  }

  Map<String, dynamic> _handleResponse(http.Response response) {
    Map<String, dynamic> json;
    try {
      json = response.body.isNotEmpty
          ? jsonDecode(response.body) as Map<String, dynamic>
          : <String, dynamic>{};
    } catch (_) {
      throw TinyHumansError(
        'HTTP ${response.statusCode}: non-JSON response',
        response.statusCode,
        response.body,
      );
    }

    if (response.statusCode < 200 || response.statusCode >= 300) {
      final message =
          json['error'] as String? ?? 'HTTP ${response.statusCode}';
      throw TinyHumansError(message, response.statusCode, response.body);
    }

    return json;
  }

  void close() {
    if (_ownsClient) {
      _httpClient.close();
    }
  }
}
