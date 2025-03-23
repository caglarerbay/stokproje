import 'package:http/http.dart' as http;
import 'dart:convert';
import 'api_constants.dart';

class AuthService {
  // Login fonksiyonu
  // Geriye bir Map döndürüyoruz: {"detail": "...", "is_staff": true/false, vb.}
  Future<Map<String, dynamic>> login(String username, String password) async {
    final url = Uri.parse("${ApiConstants.baseUrl}/api/login/");
    try {
      final response = await http.post(
        url,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: json.encode({'username': username, 'password': password}),
      );

      if (response.statusCode == 200) {
        // Giriş başarılı
        final decoded = json.decode(utf8.decode(response.bodyBytes));
        return decoded; // {"detail": "...", "is_staff": true/false, ...}
      } else {
        // Hata
        final decoded = json.decode(utf8.decode(response.bodyBytes));
        throw Exception(decoded['detail'] ?? 'Giriş hatası');
      }
    } catch (e) {
      throw Exception('Sunucuya erişilemedi. Hata: $e');
    }
  }
}
