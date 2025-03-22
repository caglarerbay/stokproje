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

  Future<void> _searchProduct() async {
    final query = _searchController.text.trim();
    if (query.isEmpty) return;

    final url = Uri.parse('http://127.0.0.1:8000/api/search_product/?q=$query');
    try {
      final response = await http.get(url);
      if (response.statusCode == 200) {
        final List data = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _searchResults = data;
        });
      } else {
        print('Arama hatası: ${response.statusCode}');
      }
    } catch (e) {
      print('Sunucuya erişilemedi: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Ana Ekran (Sadece Arama)')),
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
          // Arama sonuçları listesi
          Expanded(
            child: ListView.builder(
              itemCount: _searchResults.length,
              itemBuilder: (context, index) {
                final product = _searchResults[index];
                // product: {"id":..., "part_code":..., "name":..., "quantity":...}
                return ListTile(
                  title: Text('${product['name']}'),
                  subtitle: Text(
                    'Kod: ${product['part_code']} | Miktar: ${product['quantity']}',
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
