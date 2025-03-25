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

  // Mevcut kullanıcı listesini tutacak değişken (drop down için)
  List<String> _userList = [];

  @override
  void initState() {
    super.initState();
    _searchController.addListener(_onSearchChanged);
    // Argümanları güvenli şekilde almak için post frame callback kullanıyoruz.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final args = ModalRoute.of(context)?.settings.arguments;
      if (args is Map) {
        _isStaff = args["staff_flag"] ?? false;
        _token = args["token"];
        print("Token from arguments: $_token");
        _fetchUserList();
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
    _debounce = Timer(Duration(milliseconds: 300), _searchProduct);
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

  // Kullanıcı listesini çekiyoruz (/api/user_list/)
  Future<void> _fetchUserList() async {
    if (_token == null || _token!.isEmpty) return;
    final url = Uri.parse('${ApiConstants.baseUrl}/api/user_list/');
    final headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Token $_token',
    };
    try {
      final response = await http.get(url, headers: headers);
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _userList = List<String>.from(data['users']);
          print("Fetched users: $_userList");
        });
      } else {
        print("Kullanıcı listesi alınamadı, status: ${response.statusCode}");
      }
    } catch (e) {
      print("Kullanıcı listesi alınırken hata: $e");
    }
  }

  // Ana stoktan ürün alma (take_product endpoint)
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
        print('Ana stoktan alma işlemi başarılı');
      } else {
        final body = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _errorMessage = body['detail'] ?? 'Hata: ${response.statusCode}';
        });
        throw Exception("Take product error");
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Ana stoktan alma hatası: $e";
      });
      rethrow;
    }
  }

  // "Depodan Al" diyalogu
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
                  _searchProduct();
                },
                child: Text('Onayla'),
              ),
            ],
          ),
    );
  }

  // Kullanıcılar arası transfer (transfer_product_api endpoint)
  Future<void> _transferProduct(
    int productId,
    String targetUsername,
    int quantity,
  ) async {
    if (_token == null || _token!.isEmpty) {
      setState(() {
        _errorMessage = "Token yok, transfer işlemi yapılamaz.";
      });
      return;
    }
    final url = Uri.parse(
      '${ApiConstants.baseUrl}/api/transfer_product/$productId/',
    );
    final headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Token $_token',
    };
    final body = json.encode({
      "quantity": quantity,
      "target_username": targetUsername,
    });
    try {
      final response = await http.post(url, headers: headers, body: body);
      if (response.statusCode == 200) {
        print('Transfer işlemi başarılı');
      } else {
        final data = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _errorMessage =
              data['detail'] ?? 'Transfer hatası: ${response.statusCode}';
        });
        throw Exception("Transfer error");
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Transfer hatası: $e";
      });
      rethrow;
    }
  }

  // Direct transfer: Ana stoktan doğrudan hedef kullanıcının stoğuna aktarım yapar.
  Future<void> _directTransferProduct(
    int productId,
    String targetUsername,
    int quantity,
  ) async {
    if (_token == null || _token!.isEmpty) {
      setState(() {
        _errorMessage = "Token yok, işlem yapılamaz.";
      });
      return;
    }
    final url = Uri.parse(
      '${ApiConstants.baseUrl}/api/direct_transfer_product/$productId/',
    );
    final headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Token $_token',
    };
    final body = json.encode({
      "quantity": quantity,
      "target_username": targetUsername,
    });
    try {
      final response = await http.post(url, headers: headers, body: body);
      if (response.statusCode == 200) {
        print("Direct transfer successful");
        _searchProduct();
      } else {
        final data = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _errorMessage = data['detail'] ?? "Hata: ${response.statusCode}";
        });
        throw Exception("Direct transfer error");
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Direct transfer hatası: $e";
      });
      rethrow;
    }
  }

  // "Arkadaşına Transfer" diyalogu: Drop down menü ile mevcut kullanıcılar listeleniyor.
  void _showTransferDialog(int productId) {
    if (_userList.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            "Kullanıcı listesi boş. Lütfen daha sonra tekrar deneyin.",
          ),
        ),
      );
      return;
    }
    String? selectedUser = _userList.first;
    int quantity = 1;
    final quantityController = TextEditingController(text: "1");

    showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setStateDialog) {
            return AlertDialog(
              title: Text('Arkadaşına Transfer'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  DropdownButton<String>(
                    value: selectedUser,
                    isExpanded: true,
                    onChanged: (newValue) {
                      setStateDialog(() {
                        selectedUser = newValue;
                      });
                    },
                    items:
                        _userList.map<DropdownMenuItem<String>>((String user) {
                          return DropdownMenuItem<String>(
                            value: user,
                            child: Text(user),
                          );
                        }).toList(),
                  ),
                  TextField(
                    controller: quantityController,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(labelText: 'Miktar'),
                    onChanged: (val) {
                      quantity = int.tryParse(val) ?? 1;
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
                    if (selectedUser == null || selectedUser!.isEmpty) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text("Lütfen hedef kullanıcı seçin."),
                        ),
                      );
                      return;
                    }
                    Navigator.pop(context);
                    _directTransferProduct(productId, selectedUser!, quantity);
                  },
                  child: Text('Transfer'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  // Diğer navigasyon fonksiyonları
  void _logout() {
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
            // Admin Panel butonu (staff ise)
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
                          final partCode = product['part_code'];
                          final name = product['name'];
                          final anaStokQty = product['quantity'];
                          return ExpansionTile(
                            title: Row(
                              children: [
                                Expanded(child: Text('$name (Kod: $partCode)')),
                                // Depodan Al butonu
                                IconButton(
                                  icon: Icon(Icons.download),
                                  tooltip: 'Depodan Al',
                                  onPressed:
                                      () => _showTakeDialog(product['id']),
                                ),
                                // Arkadaşına Transfer butonu
                                IconButton(
                                  icon: Icon(Icons.send),
                                  tooltip: 'Arkadaşına Transfer',
                                  onPressed:
                                      () => _showTransferDialog(product['id']),
                                ),
                              ],
                            ),
                            subtitle: Text('Ana Stok: $anaStokQty'),
                            children: [
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
