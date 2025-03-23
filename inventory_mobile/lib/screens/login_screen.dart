import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

// YENİ: auth_service.dart import
import '../services/auth_service.dart';

class LoginScreen extends StatefulWidget {
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  String? _username;
  String? _password;
  bool _isLoading = false;
  String? _errorMessage;

  // YENİ: AuthService örneği
  final authService = AuthService();

  Future<void> _submitForm() async {
    if (!_formKey.currentState!.validate()) return;
    _formKey.currentState!.save();

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      // YENİ: authService.login(...) çağır
      final data = await authService.login(_username!, _password!);

      // Giriş başarılı => data içinde {"detail": "...", "is_staff": ...} vs.
      final bool isStaff = data['is_staff'] ?? false;

      setState(() {
        _isLoading = false;
      });

      // Ana ekrana yönlendir, isStaff'ı argument olarak gönder
      Navigator.pushReplacementNamed(context, '/home', arguments: isStaff);
    } catch (e) {
      // Hata durumunda
      setState(() {
        _isLoading = false;
        _errorMessage = e.toString(); // e.g. "Exception: Giriş hatası"
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Giriş Yap')),
      body: Padding(
        padding: EdgeInsets.all(16.0),
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
                        decoration: InputDecoration(labelText: 'Şifre'),
                        obscureText: true,
                        validator:
                            (value) => value!.isEmpty ? 'Şifre giriniz' : null,
                        onSaved: (value) => _password = value,
                      ),
                      SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _submitForm,
                        child: Text('Giriş Yap'),
                      ),
                      SizedBox(height: 8),
                      TextButton(
                        onPressed: () {
                          Navigator.pushNamed(context, '/register');
                        },
                        child: Text('Kayıt Ol'),
                      ),
                      TextButton(
                        onPressed: () {
                          Navigator.pushNamed(context, '/forgot_password');
                        },
                        child: Text('Şifremi Unuttum'),
                      ),
                    ],
                  ),
                ),
      ),
    );
  }
}
