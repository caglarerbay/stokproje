import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class TransferUsageScreen extends StatefulWidget {
  @override
  _TransferUsageScreenState createState() => _TransferUsageScreenState();
}

class _TransferUsageScreenState extends State<TransferUsageScreen> {
  List<dynamic> _myStock = [];
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fetchMyStock();
  }

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
        _errorMessage = 'Sunucuya erişilemedi: $e';
      });
    }
  }

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
      } else {
        print('Kullanım hatası: ${response.statusCode}');
      }
    } catch (e) {
      print('Sunucuya erişilemedi (useProduct): $e');
    }
  }

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
      } else {
        print('Transfer hatası: ${response.statusCode}');
      }
    } catch (e) {
      print('Sunucuya erişilemedi (transferProduct): $e');
    }
  }

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

  void _showTransferDialog(int productId) {
    int _tempQty = 1;
    String targetUser = '';
    showDialog(
      context: context,
      builder:
          (_) => AlertDialog(
            title: Text('Ürün Transferi'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  decoration: InputDecoration(labelText: 'Hedef Kullanıcı'),
                  onChanged: (val) {
                    targetUser = val.trim();
                  },
                ),
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
                  _transferProduct(productId, targetUser, _tempQty);
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
