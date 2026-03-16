class AlphahumanError implements Exception {
  final String message;
  final int status;
  final String body;

  AlphahumanError(this.message, this.status, [this.body = '']);

  @override
  String toString() => 'AlphahumanError($status): $message';
}
