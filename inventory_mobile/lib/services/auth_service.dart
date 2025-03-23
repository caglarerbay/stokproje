import 'package:http/http.dart' as http;
import 'dart:convert';
import '../utils/api_constants.dart'; // api_constants dosyan buradaysa

class AuthService {
  // Login fonksiyonu
  // Geriye bir Map döndürüyoruz: {"detail": "...", "staff_flag": true/false, "token": "..."}
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
        final decoded = json.decode(utf8.decode(response.bodyBytes));

        // Örnek dönen JSON:
        // {
        //   "detail": "Giriş başarılı.",
        //   "staff_flag": true,
        //   "token": "sjkghqwehq...jwt"
        // }

        return decoded;
      } else {
        final decoded = json.decode(utf8.decode(response.bodyBytes));
        throw Exception(decoded['detail'] ?? 'Giriş hatası');
      }
    } catch (e) {
      throw Exception('Sunucuya erişilemedi. Hata: $e');
    }
  }
}
