import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';

class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _searchController = TextEditingController();
  List<dynamic> _searchResults = [];
  String? _errorMessage;

  // Debounce timer, her karakter girişinden sonra biraz bekleyip arama yapacağız
  Timer? _debounce;

  @override
  void initState() {
    super.initState();
    // Her metin değişikliğinde _onSearchChanged tetiklenir
    _searchController.addListener(_onSearchChanged);
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _searchController.dispose();
    super.dispose();
  }

  void _onSearchChanged() {
    // Kullanıcı her karakter girdiğinde burası tetiklenir
    if (_debounce?.isActive ?? false) _debounce!.cancel();
    _debounce = Timer(Duration(milliseconds: 300), () {
      _searchProduct(); // 300 ms bekleyip arama yap
    });
  }

  Future<void> _searchProduct() async {
    final query = _searchController.text.trim();
    if (query.isEmpty) {
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
        final List data = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _errorMessage = null;
          _searchResults = data;
        });
      } else if (response.statusCode == 400) {
        final body = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _errorMessage = body['detail'] ?? "Hata: 400";
          _searchResults.clear();
        });
      } else {
        setState(() {
          _errorMessage = "Arama hatası: ${response.statusCode}";
          _searchResults.clear();
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Sunucuya erişilemedi: $e";
        _searchResults.clear();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Ana Ekran - Yazdıkça Arama')),
      body: Column(
        children: [
          // TextField - her karakterde arama
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(labelText: 'Ürün Kodu/Adı'),
            ),
          ),

          // Hata mesajı varsa göster
          if (_errorMessage != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8.0),
              child: Text(_errorMessage!, style: TextStyle(color: Colors.red)),
            ),

          // Sonuç listesi
          Expanded(
            child:
                _searchResults.isEmpty
                    ? Center(
                      child: Text('Ürün bulunamadı veya yazmaya başlayın.'),
                    )
                    : ListView.builder(
                      itemCount: _searchResults.length,
                      itemBuilder: (context, index) {
                        final product = _searchResults[index];
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
