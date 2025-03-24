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

  bool _isStaff = false;
  String? _token;

  @override
  void initState() {
    super.initState();

    // 1) Arama kutusunu dinle
    _searchController.addListener(_onSearchChanged);

    // 2) arguments'tan isStaff ve token al
    Future.microtask(() {
      final args = ModalRoute.of(context)?.settings.arguments;
      if (args is Map) {
        _isStaff = args["staff_flag"] ?? false;
        _token = args["token"];
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

    if (_token == null || _token!.isEmpty) {
      setState(() {
        _errorMessage = "Token yok, arama yapılamaz.";
      });
      return;
    }

    final url = Uri.parse(
      '${ApiConstants.baseUrl}/api/search_product/?q=$query',
    );
    final headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Token $_token',
    };

    try {
      final response = await http.get(url, headers: headers);
      if (response.statusCode == 200) {
        final List data = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _errorMessage = null;
          _searchResults = data;
        });
      } else {
        final body = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _errorMessage = body['detail'] ?? 'Hata: ${response.statusCode}';
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

  // Sadece “Depodan Al” işlemi
  Future<void> _takeProduct(int productId, int quantity) async {
    if (_token == null || _token!.isEmpty) {
      setState(() {
        _errorMessage = "Token yok, alma işlemi yapılamaz.";
      });
      return;
    }

    final url = Uri.parse(
      '${ApiConstants.baseUrl}/api/take_product/$productId/',
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
        print('Alma işlemi başarılı');
        // Listeyi yenilemek için tekrar arama
        _searchProduct();
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

  // Depodan Al miktar diyaloğu
  void _showTakeDialog(int productId) {
    int _tempQty = 1;
    showDialog(
      context: context,
      builder:
          (_) => AlertDialog(
            title: Text('Depodan Alma'),
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
                  _takeProduct(productId, _tempQty);
                },
                child: Text('Onayla'),
              ),
            ],
          ),
    );
  }

  void _logout() {
    // Token vs. sıfırlamak istiyorsanız burada yapabilirsiniz
    Navigator.pushReplacementNamed(context, '/login');
  }

  void _goToMyStock() {
    Navigator.pushNamed(
      context,
      '/my_stock_screen',
      arguments: {"token": _token, "staff_flag": _isStaff},
    );
  }

  void _goToTransferUsage() {
    Navigator.pushNamed(
      context,
      '/transfer_usage',
      arguments: {"token": _token, "staff_flag": _isStaff},
    );
  }

  void _goToAdminPanel() {
    if (_isStaff) {
      Navigator.pushNamed(
        context,
        '/admin_panel',
        arguments: {"token": _token, "staff_flag": _isStaff},
      );
    } else {
      setState(() {
        _errorMessage = "Admin Paneline erişim yok (staff_flag=false).";
      });
    }
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
            // Arama kutusu
            TextField(
              controller: _searchController,
              decoration: InputDecoration(
                labelText: 'Ürün Kodu/Adı',
                border: OutlineInputBorder(),
              ),
            ),
            SizedBox(height: 8),

            // Kişisel Stok butonu
            ElevatedButton(
              onPressed: _goToMyStock,
              child: Text('Kişisel Stok'),
            ),
            SizedBox(height: 8),

            // Transfer / Kullanım butonu
            ElevatedButton(
              onPressed: _goToTransferUsage,
              child: Text('Transfer / Kullanım'),
            ),
            SizedBox(height: 8),

            // Admin Panel butonu
            if (_isStaff)
              ElevatedButton(
                onPressed: _goToAdminPanel,
                child: Text('Admin Paneli'),
              ),

            SizedBox(height: 8),

            // Hata mesajı
            if (_errorMessage != null)
              Text(_errorMessage!, style: TextStyle(color: Colors.red)),

            // Arama sonuçları
            Expanded(
              child:
                  _searchResults.isEmpty
                      ? Center(child: Text('Hiç ürün bulunamadı.'))
                      : ListView.builder(
                        itemCount: _searchResults.length,
                        itemBuilder: (context, index) {
                          final product = _searchResults[index];
                          // product = { "id":..., "part_code":..., "name":..., "quantity":..., "car_stocks":[...] }

                          final partCode = product['part_code'];
                          final name = product['name'];
                          final anaStokQty = product['quantity'];

                          // "car_stocks" var ama bu ekranda sadece depodan al var, iade yok
                          return ExpansionTile(
                            title: Row(
                              children: [
                                Expanded(child: Text('$name (Kod: $partCode)')),
                                // Sadece depodan al butonu
                                IconButton(
                                  icon: Icon(Icons.download),
                                  tooltip: 'Depodan Al',
                                  onPressed:
                                      () => _showTakeDialog(product['id']),
                                ),
                              ],
                            ),
                            subtitle: Text('Ana Stok: $anaStokQty'),
                            children: [
                              // Kullanıcı stoklarını göstermek isterseniz:
                              if (product['car_stocks'] == null ||
                                  (product['car_stocks'] as List).isEmpty)
                                ListTile(
                                  title: Text('Bu ürünü tutan kullanıcı yok.'),
                                )
                              else
                                ...(product['car_stocks'] as List).map((cs) {
                                  final username = cs['username'];
                                  final qty = cs['quantity'];
                                  return ListTile(
                                    title: Text('Kullanıcı: $username'),
                                    subtitle: Text('Miktar: $qty'),
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
