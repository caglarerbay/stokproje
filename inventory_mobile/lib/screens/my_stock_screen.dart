import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../services/api_constants.dart';

class MyStockScreen extends StatefulWidget {
  @override
  _MyStockScreenState createState() => _MyStockScreenState();
}

class _MyStockScreenState extends State<MyStockScreen> {
  String? _token;
  bool _isStaff = false;

  List<dynamic> _myStocks = [];
  String? _errorMessage;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      final args = ModalRoute.of(context)?.settings.arguments;
      if (args is Map) {
        _token = args["token"];
        _isStaff = args["staff_flag"] ?? false;
        _fetchMyStocks();
      } else {
        setState(() {
          _errorMessage = "Token alınamadı, lütfen tekrar giriş yapın.";
        });
      }
    });
  }

  Future<void> _fetchMyStocks() async {
    if (_token == null || _token!.isEmpty) {
      setState(() {
        _errorMessage = "Token yok, kendi stoğunuzu çekemiyoruz.";
      });
      return;
    }
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final url = Uri.parse('${ApiConstants.baseUrl}/api/my_stock/');
    final headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Token $_token',
    };

    try {
      final response = await http.get(url, headers: headers);
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        final List<dynamic> stocks = data["stocks"] ?? [];

        // 0 adet olanları ayıklıyoruz
        final filtered =
            stocks.where((item) {
              final qty = item["quantity"] ?? 0;
              return qty > 0;
            }).toList();

        setState(() {
          _myStocks = filtered;
          _isLoading = false;
        });
      } else {
        final body = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _errorMessage = body['detail'] ?? 'Hata: ${response.statusCode}';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Sunucuya erişilemedi: $e";
        _isLoading = false;
      });
    }
  }

  // Depoya Bırak fonksiyonu
  Future<void> _returnProduct(int productId, int quantity) async {
    if (_token == null || _token!.isEmpty) {
      setState(() {
        _errorMessage = "Token yok, bırakamıyoruz.";
      });
      return;
    }

    final url = Uri.parse(
      '${ApiConstants.baseUrl}/api/return_product/$productId/',
    );
    final headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Token $_token',
    };

    try {
      final response = await http.post(
        url,
        headers: headers,
        body: json.encode({'quantity': quantity}),
      );
      if (response.statusCode == 200) {
        print('Depoya Bırakma başarılı');
        // Stoğu yenile
        _fetchMyStocks();
      } else {
        final body = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _errorMessage = body['detail'] ?? 'Hata: ${response.statusCode}';
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Sunucuya erişilemedi: $e";
      });
    }
  }

  void _showReturnDialog(int productId) {
    int _tempQty = 1;
    showDialog(
      context: context,
      builder:
          (_) => AlertDialog(
            title: Text('Depoya Bırak'),
            content: TextField(
              keyboardType: TextInputType.number,
              decoration: InputDecoration(labelText: 'Miktar'),
              onChanged: (val) {
                _tempQty = int.tryParse(val) ?? 1;
              },
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: Text('İptal'),
              ),
              TextButton(
                onPressed: () {
                  Navigator.pop(context);
                  _returnProduct(productId, _tempQty);
                },
                child: Text('Onayla'),
              ),
            ],
          ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Kişisel Stok')),
      body:
          _isLoading
              ? Center(child: CircularProgressIndicator())
              : _errorMessage != null
              ? Center(
                child: Text(
                  _errorMessage!,
                  style: TextStyle(color: Colors.red),
                ),
              )
              : _myStocks.isEmpty
              ? Center(child: Text('Stokta ürün bulunamadı (veya 0 adet).'))
              : ListView.builder(
                itemCount: _myStocks.length,
                itemBuilder: (context, index) {
                  final item = _myStocks[index];
                  final productId = item["product_id"];
                  final productName = item["product_name"];
                  final partCode = item["part_code"];
                  final qty = item["quantity"];

                  return ListTile(
                    title: Text('$productName (Kod: $partCode)'),
                    subtitle: Text('Miktar: $qty'),
                    trailing: IconButton(
                      icon: Icon(Icons.upload),
                      tooltip: 'Depoya Bırak',
                      onPressed: () => _showReturnDialog(productId),
                    ),
                  );
                },
              ),
    );
  }
}
