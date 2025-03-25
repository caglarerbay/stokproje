import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../services/api_constants.dart';

class AdminUserStocksScreen extends StatefulWidget {
  @override
  _AdminUserStocksScreenState createState() => _AdminUserStocksScreenState();
}

class _AdminUserStocksScreenState extends State<AdminUserStocksScreen> {
  String? _token;
  bool _isStaff = false;

  String? _errorMessage;
  List<dynamic> _userStocks = [];

  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      final args = ModalRoute.of(context)?.settings.arguments;
      if (args is Map) {
        _token = args["token"];
        _isStaff = args["staff_flag"] ?? false;

        _fetchUserStocks();
      } else {
        setState(() {
          _errorMessage = "Token veya staff_flag alınamadı.";
        });
      }
    });
  }

  Future<void> _fetchUserStocks() async {
    if (_token == null || _token!.isEmpty) {
      setState(() {
        _errorMessage = "Token yok, admin_user_stocks için giriş gerekli.";
      });
      return;
    }

    final url = Uri.parse(
      '${ApiConstants.baseUrl}/api/admin_list_user_stocks/',
    );
    final headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Token $_token',
    };

    try {
      final response = await http.get(url, headers: headers);
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _userStocks = data['user_stocks'] as List<dynamic>;
        });
      } else {
        final body = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _errorMessage = body['detail'] ?? 'Hata: ${response.statusCode}';
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Sunucu hatası: $e";
      });
    }
  }

  Future<void> _updateUserStock(
    String username,
    String partCode,
    int newQuantity,
  ) async {
    final url = Uri.parse(
      '${ApiConstants.baseUrl}/api/admin_adjust_user_stock/',
    );
    final headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Token $_token',
    };
    final body = json.encode({
      "username": username,
      "part_code": partCode,
      "new_quantity": newQuantity,
    });
    try {
      final response = await http.post(url, headers: headers, body: body);
      if (response.statusCode == 200) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text("Stok güncellendi.")));
        _fetchUserStocks();
      } else {
        final data = json.decode(utf8.decode(response.bodyBytes));
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              data['detail'] ?? 'Güncelleme hatası: ${response.statusCode}',
            ),
          ),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text("Sunucu hatası: $e")));
    }
  }

  void _showUpdateDialog(
    String username,
    String partCode,
    int currentQuantity,
  ) {
    final _controller = TextEditingController(text: currentQuantity.toString());
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text("Stok Güncelle - $partCode"),
          content: TextField(
            controller: _controller,
            keyboardType: TextInputType.number,
            decoration: InputDecoration(labelText: "Yeni Miktar"),
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(context);
              },
              child: Text("İptal"),
            ),
            TextButton(
              onPressed: () {
                final input = _controller.text;
                final newQuantity = int.tryParse(input);
                if (newQuantity == null) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text("Lütfen geçerli bir sayı girin.")),
                  );
                  return;
                }
                Navigator.pop(context);
                _updateUserStock(username, partCode, newQuantity);
              },
              child: Text("Güncelle"),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Kullanıcı Stokları')),
      body:
          _errorMessage != null
              ? Center(
                child: Text(
                  _errorMessage!,
                  style: TextStyle(color: Colors.red),
                ),
              )
              : ListView.builder(
                itemCount: _userStocks.length,
                itemBuilder: (context, index) {
                  final userObj = _userStocks[index];
                  final username = userObj['username'];
                  final stocks = userObj['stocks'] as List<dynamic>;

                  return ExpansionTile(
                    title: Text('Kullanıcı: $username'),
                    children: [
                      if (stocks.isEmpty)
                        ListTile(title: Text('Bu kullanıcının stoğu yok.'))
                      else
                        ...stocks.map((stockItem) {
                          return ListTile(
                            title: Text('Ürün: ${stockItem['part_code']}'),
                            subtitle: Text('Miktar: ${stockItem['quantity']}'),
                            trailing: IconButton(
                              icon: Icon(Icons.edit),
                              onPressed: () {
                                _showUpdateDialog(
                                  username,
                                  stockItem['part_code'],
                                  stockItem['quantity'],
                                );
                              },
                            ),
                          );
                        }).toList(),
                    ],
                  );
                },
              ),
    );
  }
}
