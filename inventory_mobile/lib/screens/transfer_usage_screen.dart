import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';

class TransferUsageScreen extends StatefulWidget {
  @override
  _TransferUsageScreenState createState() => _TransferUsageScreenState();
}

class _TransferUsageScreenState extends State<TransferUsageScreen> {
  // 1) Kişisel stok listesi
  List<dynamic> _myStock = [];

  // 2) Tüm kullanıcılar listesi (hedef kullanıcı seçmek için)
  List<String> _users = [];

  // Hata mesajını göstermek istersen
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    // Ekran açıldığında stoğumu çek + user list çek
    _fetchMyStock();
    _fetchUsers();
  }

  // 3) Kişisel stoğu çek
  Future<void> _fetchMyStock() async {
    final url = Uri.parse('http://127.0.0.1:8000/api/my_stock/');
    try {
      final response = await http.get(url);
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _myStock = data['stocks'] as List<dynamic>;
          _errorMessage = null;
        });
      } else {
        setState(() {
          _errorMessage = 'Stok çekme hatası: ${response.statusCode}';
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Sunucuya erişilemedi (my_stock): $e';
      });
    }
  }

  // 4) Kullanıcı listesini çek
  Future<void> _fetchUsers() async {
    final url = Uri.parse('http://127.0.0.1:8000/api/user_list/');
    try {
      final response = await http.get(url);
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        final List<dynamic> userList = data['users'];
        setState(() {
          _users = userList.map((u) => u.toString()).toList();
          _users.remove("testuser"); // sabit user'ı listeden çıkar
        });
      } else {
        print('Kullanıcı listesi çekme hatası: ${response.statusCode}');
      }
    } catch (e) {
      print('Sunucuya erişilemedi (user_list): $e');
    }
  }

  // 5) Kullanım isteği
  Future<void> _useProduct(int productId, int qty) async {
    final url = Uri.parse('http://127.0.0.1:8000/api/use_product/$productId/');
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'quantity': qty}),
      );
      if (response.statusCode == 200) {
        print('Kullanım başarılı');
        _fetchMyStock(); // stoğu yenile
      } else if (response.statusCode == 400) {
        // Hata mesajı
        final body = json.decode(utf8.decode(response.bodyBytes));
        final detail = body['detail'] ?? 'Bilinmeyen hata';
        _showErrorDialog(detail);
      } else {
        print('Kullanım hatası: ${response.statusCode}');
      }
    } catch (e) {
      print('Sunucuya erişilemedi (useProduct): $e');
    }
  }

  // 6) Transfer isteği
  Future<void> _transferProduct(
    int productId,
    String targetUser,
    int qty,
  ) async {
    final url = Uri.parse(
      'http://127.0.0.1:8000/api/transfer_product/$productId/',
    );
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'quantity': qty, 'target_username': targetUser}),
      );
      if (response.statusCode == 200) {
        print('Transfer başarılı');
        _fetchMyStock();
      } else if (response.statusCode == 400) {
        final body = json.decode(utf8.decode(response.bodyBytes));
        final detail = body['detail'] ?? 'Bilinmeyen hata';
        _showErrorDialog(detail);
      } else {
        print('Transfer hatası: ${response.statusCode}');
      }
    } catch (e) {
      print('Sunucuya erişilemedi (transferProduct): $e');
    }
  }

  // 7) Kullanım diyalogu
  void _showUseDialog(int productId) {
    int _tempQty = 1;
    showDialog(
      context: context,
      builder:
          (_) => AlertDialog(
            title: Text('Ürün Kullanımı'),
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
                  _useProduct(productId, _tempQty);
                },
                child: Text('Onayla'),
              ),
            ],
          ),
    );
  }

  // 8) Transfer diyalogu (dropdown)
  void _showTransferDialog(int productId) {
    int _tempQty = 1;
    String? _selectedUser; // diyalog içi değişken

    showDialog(
      context: context,
      builder: (_) {
        return StatefulBuilder(
          builder: (dialogContext, setStateDialog) {
            return AlertDialog(
              title: Text('Ürün Transferi'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Dropdown
                  DropdownButton<String>(
                    hint: Text('Hedef Kullanıcı Seç'),
                    value: _selectedUser,
                    items:
                        _users.map((user) {
                          return DropdownMenuItem<String>(
                            value: user,
                            child: Text(user),
                          );
                        }).toList(),
                    onChanged: (val) {
                      // Bu setStateDialog, dialog içi yenileme
                      setStateDialog(() {
                        _selectedUser = val;
                      });
                    },
                  ),
                  // Miktar
                  TextField(
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(labelText: 'Miktar'),
                    onChanged: (val) {
                      _tempQty = int.tryParse(val) ?? 1;
                    },
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: Text('İptal'),
                ),
                TextButton(
                  onPressed: () {
                    Navigator.pop(context);
                    if (_selectedUser == null) {
                      _showErrorDialog('Lütfen hedef kullanıcı seçin.');
                    } else {
                      _transferProduct(productId, _selectedUser!, _tempQty);
                    }
                  },
                  child: Text('Onayla'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  // 9) Hata diyaloğu
  void _showErrorDialog(String message) {
    showDialog(
      context: context,
      builder:
          (_) => AlertDialog(
            title: Text('Hata'),
            content: Text(message),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: Text('Tamam'),
              ),
            ],
          ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Transfer / Kullanım Ekranı')),
      body:
          _errorMessage != null
              ? Center(child: Text(_errorMessage!))
              : ListView.builder(
                itemCount: _myStock.length,
                itemBuilder: (context, index) {
                  final item = _myStock[index];
                  // item = { "product_id":..., "part_code":..., "product_name":..., "quantity":... }
                  return ListTile(
                    title: Text(
                      '${item['product_name']} (Kod: ${item['part_code']})',
                    ),
                    subtitle: Text('Miktar: ${item['quantity']}'),
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        IconButton(
                          icon: Icon(Icons.build), // Kullanım ikonu
                          tooltip: 'Kullanım',
                          onPressed: () => _showUseDialog(item['product_id']),
                        ),
                        IconButton(
                          icon: Icon(Icons.swap_horiz), // Transfer ikonu
                          tooltip: 'Transfer',
                          onPressed:
                              () => _showTransferDialog(item['product_id']),
                        ),
                      ],
                    ),
                  );
                },
              ),
    );
  }
}
