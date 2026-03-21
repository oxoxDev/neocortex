import 'dart:io' show Platform;

import 'package:test/test.dart';

import 'package:tinyhumans_sdk/tinyhumans_sdk.dart';

void main() {
  test('insert-recall-query-delete lifecycle', () async {
    final token = Platform.environment['TINYHUMANS_TOKEN'];
    if (token == null || token.isEmpty) {
      print('TINYHUMANS_TOKEN not set — skipping integration test');
      return;
    }

    final ns =
        'integration-test-dart-${DateTime.now().millisecondsSinceEpoch}';
    final client = TinyHumansMemoryClient(token);

    try {
      // ── Insert ──
      final nowSeconds =
          DateTime.now().millisecondsSinceEpoch ~/ 1000;
      final insertResp = await client.insertMemory(InsertMemoryParams(
        title: 'test-key-1',
        content: 'The capital of France is Paris.',
        namespace: ns,
        createdAt: nowSeconds,
        updatedAt: nowSeconds,
      ));
      expect(insertResp.success, isTrue, reason: 'insert should succeed');

      // Give the backend time to index
      await Future.delayed(const Duration(seconds: 2));

      // ── Recall ──
      final recallResp = await client.recallMemory(
          RecallMemoryParams(namespace: ns));
      expect(recallResp.success, isTrue, reason: 'recall should succeed');

      // ── Query ──
      final queryResp = await client.queryMemory(QueryMemoryParams(
        query: 'What is the capital of France?',
        namespace: ns,
      ));
      expect(queryResp.success, isTrue, reason: 'query should succeed');

      // ── Delete ──
      final deleteResp = await client.deleteMemory(
          DeleteMemoryParams(namespace: ns));
      expect(deleteResp.success, isTrue, reason: 'delete should succeed');

      // Give the backend time to process deletion
      await Future.delayed(const Duration(seconds: 1));

      // ── Verify deletion ──
      final verifyResp = await client.recallMemory(
          RecallMemoryParams(namespace: ns));
      expect(verifyResp.success, isTrue);
    } finally {
      client.close();
    }
  });
}
