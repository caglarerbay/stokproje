import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';
import '../services/api_constants.dart';

class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _searchController = TextEditingController();
  List<dynamic> _searchResults = [];
  String? _errorMessage;
  Timer? _debounce;

  // Admin veya normal kullanıcı?
  bool _isStaff = false;

  // Login ekranından aldığımız token
  String? _token;

  @override
  void initState() {
    super.initState();

    // Arama kutusu her değiştiğinde _onSearchChanged
    _searchController.addListener(_onSearchChanged);

    // arguments'dan isStaff ve token alalım
    Future.microtask(() {
      final args = ModalRoute.of(context)?.settings.arguments;
      if (args is Map) {
        // Örn: { "token": "...", "staff_flag": true }
        setState(() {
          _isStaff = args["staff_flag"] ?? false;
          _token = args["token"]; // login_screen.dart'tan gelen token
        });
      }
    });
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _searchController.dispose();
    super.dispose();
  }

  void _onSearchChanged() {
    if (_debounce?.isActive ?? false) _debounce!.cancel();
    _debounce = Timer(Duration(milliseconds: 300), () {
      _searchProduct();
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

    final url = Uri.parse(
      '${ApiConstants.baseUrl}/api/search_product/?q=$query',
    );

    try {
      // Eğer endpoint IsAuthenticated ise token header ekleyin:
      // _token boş mu kontrol edebilirsiniz:
      final headers = {'Content-Type': 'application/json'};
      if (_token != null && _token!.isNotEmpty) {
        headers['Authorization'] = 'Token $_token';
      }

      final response = await http.get(url, headers: headers);

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

  Future<void> _takeProduct(int productId, int quantity) async {
    final url = Uri.parse(
      '${ApiConstants.baseUrl}/api/take_product/$productId/',
    );
    try {
      // Token eklemek isterseniz yine ekleyebilirsiniz:
      final headers = {'Content-Type': 'application/json'};
      if (_token != null && _token!.isNotEmpty) {
        headers['Authorization'] = 'Token $_token';
      }

      final response = await http.post(
        url,
        headers: headers,
        body: json.encode({'quantity': quantity}),
      );

      if (response.statusCode == 200) {
        print('Alma işlemi başarılı');
        _searchProduct(); // Yeniden arama
      } else {
        print('Alma işlemi hatası: ${response.statusCode}');
      }
    } catch (e) {
      print('Sunucuya erişilemedi (takeProduct): $e');
    }
  }

  Future<void> _returnProduct(int productId, int quantity) async {
    final url = Uri.parse(
      '${ApiConstants.baseUrl}/api/return_product/$productId/',
    );
    try {
      final headers = {'Content-Type': 'application/json'};
      if (_token != null && _token!.isNotEmpty) {
        headers['Authorization'] = 'Token $_token';
      }

      final response = await http.post(
        url,
        headers: headers,
        body: json.encode({'quantity': quantity}),
      );
      if (response.statusCode == 200) {
        print('Bırakma işlemi başarılı');
        _searchProduct();
      } else {
        print('Bırakma işlemi hatası: ${response.statusCode}');
      }
    } catch (e) {
      print('Sunucuya erişilemedi (returnProduct): $e');
    }
  }

  void _showQuantityDialog(bool isTake, int productId) {
    int _tempQty = 1;
    showDialog(
      context: context,
      builder:
          (_) => AlertDialog(
            title: Text(isTake ? 'Depodan Alma' : 'Depoya Bırakma'),
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
                  if (isTake) {
                    _takeProduct(productId, _tempQty);
                  } else {
                    _returnProduct(productId, _tempQty);
                  }
                },
                child: Text('Onayla'),
              ),
            ],
          ),
    );
  }

  void _logout() {
    // Burada token vs. silmek isterseniz yapabilirsiniz
    // Sonra login ekranına geri dönelim
    Navigator.pushReplacementNamed(context, '/login');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Ana Ekran'),
        actions: [
          IconButton(
            icon: Icon(Icons.exit_to_app),
            tooltip: 'Çıkış Yap',
            onPressed: _logout,
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(8.0),
        child: Column(
          children: [
            // Arama kutusu boydan boya
            TextField(
              controller: _searchController,
              decoration: InputDecoration(
                labelText: 'Ürün Kodu/Adı',
                border: OutlineInputBorder(),
              ),
            ),
            SizedBox(height: 8),

            // Transfer/Kullanım butonu
            ElevatedButton(
              onPressed: () {
                Navigator.pushNamed(
                  context,
                  '/transfer_usage',
                  arguments: {"token": _token, "staff_flag": _isStaff},
                );
              },
              child: Text('Transfer / Kullanım'),
            ),

            SizedBox(height: 8),

            // Admin Panel butonu (sadece isStaff true ise)
            if (_isStaff)
              ElevatedButton(
                onPressed: () {
                  Navigator.pushNamed(
                    context,
                    '/admin_panel',
                    arguments: {"token": _token, "staff_flag": _isStaff},
                  );
                },
                child: Text('Admin Paneli'),
              ),

            SizedBox(height: 8),

            // Hata mesajı varsa göster
            if (_errorMessage != null)
              Text(_errorMessage!, style: TextStyle(color: Colors.red)),

            // Sonuç listesi
            Expanded(
              child:
                  _searchResults.isEmpty
                      ? Center(child: Text('Hiç ürün bulunamadı.'))
                      : ListView.builder(
                        itemCount: _searchResults.length,
                        itemBuilder: (context, index) {
                          final product = _searchResults[index];
                          final carStocks =
                              product['car_stocks'] as List<dynamic>? ?? [];

                          return ExpansionTile(
                            title: Row(
                              children: [
                                Expanded(
                                  child: Text(
                                    '${product['name']} (Kod: ${product['part_code']})',
                                  ),
                                ),
                                IconButton(
                                  icon: Icon(Icons.download),
                                  tooltip: 'Depodan Al',
                                  onPressed:
                                      () => _showQuantityDialog(
                                        true,
                                        product['id'],
                                      ),
                                ),
                                IconButton(
                                  icon: Icon(Icons.upload),
                                  tooltip: 'Depoya Bırak',
                                  onPressed:
                                      () => _showQuantityDialog(
                                        false,
                                        product['id'],
                                      ),
                                ),
                              ],
                            ),
                            subtitle: Text('Ana Stok: ${product['quantity']}'),
                            children: [
                              if (carStocks.isEmpty)
                                ListTile(
                                  title: Text('Bu ürünü tutan kullanıcı yok.'),
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
      ),
    );
  }
}
