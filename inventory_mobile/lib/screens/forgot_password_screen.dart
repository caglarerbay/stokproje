import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class ForgotPasswordScreen extends StatefulWidget {
  @override
  _ForgotPasswordScreenState createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  String? _username;
  String? _accessCode;
  String? _newPassword;
  String? _newPassword2;
  bool _isLoading = false;
  String? _errorMessage;

  Future<void> _submitForm() async {
    if (!_formKey.currentState!.validate()) return;
    _formKey.currentState!.save();

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final url = Uri.parse(
      'http://127.0.0.1:8000/api/forgot_password/',
    ); // Django endpoint
    try {
      final response = await http.post(
        url,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: json.encode({
          'username': _username,
          'access_code': _accessCode,
          'new_password': _newPassword,
          'new_password2': _newPassword2,
        }),
      );

      if (response.statusCode == 200) {
        setState(() {
          _isLoading = false;
        });
        // Şifre güncellendi, login ekranına dönebiliriz
        showDialog(
          context: context,
          builder:
              (_) => AlertDialog(
                title: Text('Başarılı'),
                content: Text('Şifreniz güncellendi.'),
                actions: [
                  TextButton(
                    onPressed: () {
                      Navigator.pop(context); // AlertDialog kapanır
                      Navigator.pushReplacementNamed(context, '/login');
                    },
                    child: Text('Tamam'),
                  ),
                ],
              ),
        );
      } else {
        setState(() {
          _isLoading = false;
          final decoded = json.decode(utf8.decode(response.bodyBytes));
          _errorMessage = decoded['detail'] ?? 'Hata oluştu';
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
      appBar: AppBar(title: Text('Şifremi Unuttum')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child:
            _isLoading
                ? Center(child: CircularProgressIndicator())
                : Form(
                  key: _formKey,
                  child: ListView(
                    children: [
                      if (_errorMessage != null)
                        Text(
                          _errorMessage!,
                          style: TextStyle(color: Colors.red),
                        ),
                      TextFormField(
                        decoration: InputDecoration(labelText: 'Kullanıcı Adı'),
                        validator:
                            (value) =>
                                value!.isEmpty ? 'Kullanıcı adı giriniz' : null,
                        onSaved: (value) => _username = value,
                      ),
                      TextFormField(
                        decoration: InputDecoration(labelText: '10 Haneli Kod'),
                        validator:
                            (value) => value!.isEmpty ? 'Kod giriniz' : null,
                        onSaved: (value) => _accessCode = value,
                      ),
                      TextFormField(
                        decoration: InputDecoration(labelText: 'Yeni Şifre'),
                        obscureText: true,
                        validator:
                            (value) =>
                                value!.isEmpty ? 'Yeni şifre giriniz' : null,
                        onSaved: (value) => _newPassword = value,
                      ),
                      TextFormField(
                        decoration: InputDecoration(
                          labelText: 'Yeni Şifre (Tekrar)',
                        ),
                        obscureText: true,
                        validator:
                            (value) =>
                                value!.isEmpty ? 'Şifre tekrar giriniz' : null,
                        onSaved: (value) => _newPassword2 = value,
                      ),
                      SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _submitForm,
                        child: Text('Şifreyi Güncelle'),
                      ),
                    ],
                  ),
                ),
      ),
    );
  }
}
