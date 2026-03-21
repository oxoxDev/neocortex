class TinyHumansError implements Exception {
  final String message;
  final int status;
  final String body;

  TinyHumansError(this.message, this.status, [this.body = '']);

  @override
  String toString() => 'TinyHumansError($status): $message';
}
