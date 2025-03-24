import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../services/api_constants.dart';

class AdminAddProductScreen extends StatefulWidget {
  @override
  _AdminAddProductScreenState createState() => _AdminAddProductScreenState();
}

class _AdminAddProductScreenState extends State<AdminAddProductScreen> {
  final _formKey = GlobalKey<FormState>();
  String _partCode = '';
  String _name = '';
  int _quantity = 0;
  String? _errorMessage;

  // BURADA TOKEN TUTACAĞIZ
  String? _token;

  @override
  void initState() {
    super.initState();

    // arguments'tan token'ı alalım
    Future.microtask(() {
      final args = ModalRoute.of(context)?.settings.arguments;
      if (args is Map) {
        // Örnek: { "token": "...", "staff_flag": true }
        _token = args["token"];
      } else {
        setState(() {
          _errorMessage = "Token alınamadı. Lütfen tekrar giriş yapın.";
        });
      }
    });
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    _formKey.currentState!.save();

    if (_token == null || _token!.isEmpty) {
      setState(() {
        _errorMessage = "Token yok, admin_add_product için giriş gerekli.";
      });
      return;
    }

    final url = Uri.parse('${ApiConstants.baseUrl}/api/admin_add_product/');

    // Token header
    final headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Token $_token', // <-- ÖNEMLİ
    };

    try {
      final response = await http.post(
        url,
        headers: headers,
        body: json.encode({
          'part_code': _partCode,
          'name': _name,
          'quantity': _quantity,
        }),
      );
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        print("admin_add_product detail: ${data['detail']}");
        Navigator.pop(context); // Ekrandan çık
      } else {
        // Hata
        final body = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _errorMessage = body['detail'] ?? 'Hata: ${response.statusCode}';
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Sunucuya erişilemedi: $e';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Ürün Ekle')),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: ListView(
            children: [
              if (_errorMessage != null)
                Text(_errorMessage!, style: TextStyle(color: Colors.red)),
              TextFormField(
                decoration: InputDecoration(labelText: 'Parça Kodu'),
                validator: (val) => val!.isEmpty ? 'Parça kodu zorunlu' : null,
                onSaved: (val) => _partCode = val!.trim(),
              ),
              TextFormField(
                decoration: InputDecoration(labelText: 'Ürün Adı'),
                validator: (val) => val!.isEmpty ? 'Ürün adı zorunlu' : null,
                onSaved: (val) => _name = val!.trim(),
              ),
              TextFormField(
                decoration: InputDecoration(labelText: 'Miktar'),
                keyboardType: TextInputType.number,
                validator: (val) => val!.isEmpty ? 'Miktar zorunlu' : null,
                onSaved: (val) => _quantity = int.tryParse(val!) ?? 0,
              ),
              SizedBox(height: 16),
              ElevatedButton(onPressed: _submit, child: Text('Kaydet')),
            ],
          ),
        ),
      ),
    );
  }
}
