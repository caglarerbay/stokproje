import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class RegisterScreen extends StatefulWidget {
  @override
  _RegisterScreenState createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  String? _username;
  String? _email;
  String? _accessCode;
  String? _password;
  String? _password2;
  bool _isLoading = false;
  String? _errorMessage;

  Future<void> _submitForm() async {
    // Form doğrulaması
    if (!_formKey.currentState!.validate()) return;
    _formKey.currentState!.save();

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final url = Uri.parse('http://127.0.0.1:8000/api/register/'); 
    // Yukarıdaki URL, Django tarafında /api/register/ endpoint'ine işaret etmeli.

    try {
      final response = await http.post(
        url,
        headers: {
          'Accept': 'application/json',      // JSON formatı talep ediyoruz
          'Content-Type': 'application/json' // JSON gönderiyoruz
        },
        body: json.encode({
          'username': _username,
          'email': _email,
          'access_code': _accessCode,
          'password': _password,
          'password2': _password2, // Opsiyonel doğrulama
        }),
      );

      if (response.statusCode == 201) {
        // Kayıt başarılı
        setState(() {
          _isLoading = false;
        });
        // İsterseniz başka bir ekrana yönlendirin veya mesaj gösterin
        Navigator.pop(context);
      } else {
        // Hata durumu
        setState(() {
          _isLoading = false;
          // Yanıtı UTF-8 decode ederek Türkçe karakter sorununu önlüyoruz
          final decoded = json.decode(utf8.decode(response.bodyBytes));
          // Örneğin {"detail": "Geçersiz erişim kodu."}
          _errorMessage = decoded['detail'] ?? 'Bilinmeyen hata.';
        });
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
        _errorMessage = 'Sunucuya erişilemedi. Hata: $e';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Kayıt Ol'),
      ),
      body: Padding(
        padding: EdgeInsets.all(16.0),
        child: _isLoading
            ? Center(child: CircularProgressIndicator())
            : Form(
                key: _formKey,
                child: ListView(
                  children: [
                    // Hata mesajı
                    if (_errorMessage != null)
                      Text(
                        _errorMessage!,
                        style: TextStyle(color: Colors.red),
                      ),
                    // Kullanıcı adı
                    TextFormField(
                      decoration: InputDecoration(labelText: 'Kullanıcı Adı'),
                      validator: (value) =>
                          value!.isEmpty ? 'Kullanıcı adı giriniz' : null,
                      onSaved: (value) => _username = value,
                    ),
                    // Email
                    TextFormField(
                      decoration: InputDecoration(labelText: 'Email'),
                      validator: (value) =>
                          value!.isEmpty ? 'Email giriniz' : null,
                      onSaved: (value) => _email = value,
                    ),
                    // 10 haneli kod
                    TextFormField(
                      decoration: InputDecoration(labelText: '10 Haneli Kod'),
                      validator: (value) =>
                          value!.isEmpty ? 'Kod giriniz' : null,
                      onSaved: (value) => _accessCode = value,
                    ),
                    // Şifre
                    TextFormField(
                      decoration: InputDecoration(labelText: 'Şifre'),
                      obscureText: true,
                      validator: (value) =>
                          value!.isEmpty ? 'Şifre giriniz' : null,
                      onSaved: (value) => _password = value,
                    ),
                    // Şifre (Tekrar) - Opsiyonel
                    TextFormField(
                      decoration: InputDecoration(labelText: 'Şifre (Tekrar)'),
                      obscureText: true,
                      onSaved: (value) => _password2 = value,
                    ),
                    SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: _submitForm,
                      child: Text('Kayıt Ol'),
                    ),
                  ],
                ),
              ),
      ),
    );
  }
}
