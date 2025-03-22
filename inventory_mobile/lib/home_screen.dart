import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _searchController = TextEditingController();
  List<dynamic> _searchResults = [];

  String? _errorMessage; // Arama veya sunucu hataları için

  Future<void> _searchProduct() async {
    final query = _searchController.text.trim();
    if (query.isEmpty) {
      // Lokal uyarı: Arama terimi boş
      setState(() {
        _errorMessage = "Arama terimi boş olamaz.";
        _searchResults.clear();
      });
      return;
    }

    final url = Uri.parse('http://127.0.0.1:8000/api/search_product/?q=$query');
    try {
      final response = await http.get(url);

      if (response.statusCode == 200) {
        // Başarılı
        final List data = json.decode(utf8.decode(response.bodyBytes));
        // data boş olabilir -> ürün bulunamadı
        setState(() {
          _errorMessage = null; // varsa hata temizle
          _searchResults = data; // data boşsa listView de boş olur
        });
      } else if (response.statusCode == 400) {
        // Arama terimi boş, ya da başka 400 durumu
        final body = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _errorMessage = body['detail'] ?? "Hata: 400";
          _searchResults.clear();
        });
      } else {
        // Diğer hatalar
        setState(() {
          _errorMessage = "Arama hatası: ${response.statusCode}";
          _searchResults.clear();
        });
      }
    } catch (e) {
      // Sunucuya erişilemedi vs.
      setState(() {
        _errorMessage = "Sunucuya erişilemedi: $e";
        _searchResults.clear();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Ana Ekran - Arama & car_stocks')),
      body: Column(
        children: [
          // Arama kutusu
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _searchController,
                    decoration: InputDecoration(labelText: 'Ürün Kodu/Adı'),
                  ),
                ),
                ElevatedButton(onPressed: _searchProduct, child: Text('Ara')),
              ],
            ),
          ),

          // Hata mesajı göster
          if (_errorMessage != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8.0),
              child: Text(_errorMessage!, style: TextStyle(color: Colors.red)),
            ),

          // Sonuçlar
          Expanded(
            child:
                _searchResults.isEmpty
                    ? Center(
                      child: Text(
                        'Ürün bulunamadı veya henüz arama yapılmadı.',
                      ),
                    )
                    : ListView.builder(
                      itemCount: _searchResults.length,
                      itemBuilder: (context, index) {
                        final product = _searchResults[index];
                        // product = {
                        //   "id": ...,
                        //   "part_code": ...,
                        //   "name": ...,
                        //   "quantity": ...,
                        //   "car_stocks": [
                        //      {"username": "caglar", "quantity": 2},
                        //      {"username": "kuzu", "quantity": 3},
                        //   ]
                        // }
                        final carStocks =
                            product['car_stocks'] as List<dynamic>? ?? [];

                        return ExpansionTile(
                          title: Text('${product['name']}'),
                          subtitle: Text(
                            'Kod: ${product['part_code']} | Ana Stok: ${product['quantity']}',
                          ),
                          children: [
                            if (carStocks.isEmpty)
                              ListTile(
                                title: Text(
                                  'Bu ürünü tutan kullanıcı stoğu yok.',
                                ),
                              )
                            else
                              ...carStocks.map((cs) {
                                // cs = {"username": "...", "quantity": ...}
                                return ListTile(
                                  title: Text('Kullanıcı: ${cs['username']}'),
                                  subtitle: Text('Miktar: ${cs['quantity']}'),
                                );
                              }).toList(),
                          ],
                        );
                      },
                    ),
          ),
        ],
      ),
    );
  }
}
