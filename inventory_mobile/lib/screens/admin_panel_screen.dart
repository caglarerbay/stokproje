import 'package:flutter/material.dart';

class AdminPanelScreen extends StatefulWidget {
  @override
  _AdminPanelScreenState createState() => _AdminPanelScreenState();
}

class _AdminPanelScreenState extends State<AdminPanelScreen> {
  bool _isStaff = false;
  String? _token;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();

    // arguments'tan token ve staff_flag alalım
    Future.microtask(() {
      final args = ModalRoute.of(context)?.settings.arguments;
      if (args is Map) {
        _token = args["token"];
        _isStaff = args["staff_flag"] ?? false;

        // İsteğe bağlı kontrol
        if (_token == null || _token!.isEmpty) {
          setState(() {
            _errorMessage = "Admin Panel: Token boş veya null.";
          });
        } else if (!_isStaff) {
          // Eğer staff değilse uyarı
          setState(() {
            _errorMessage =
                "Uyarı: Admin değilsiniz. Bazı işlemler kısıtlı olabilir.";
          });
        }
      } else {
        setState(() {
          _errorMessage = "Admin Panel: arguments bulunamadı.";
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Admin Paneli')),
      body: ListView(
        padding: EdgeInsets.all(16),
        children: [
          if (_errorMessage != null)
            Text(_errorMessage!, style: TextStyle(color: Colors.red)),
          SizedBox(height: 16),

          Text(
            'Hoş geldin, Admin!',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          SizedBox(height: 16),

          // Ürün Ekle
          ElevatedButton(
            onPressed: () {
              // /admin_add_product ekranına giderken token ve staff_flag'i yine arguments'ta gönderiyoruz
              Navigator.pushNamed(
                context,
                '/admin_add_product',
                arguments: {"token": _token, "staff_flag": _isStaff},
              );
            },
            child: Text('Ürün Ekle'),
          ),
          SizedBox(height: 8),

          // Stok Güncelle
          ElevatedButton(
            onPressed: () {
              Navigator.pushNamed(
                context,
                '/admin_update_stock',
                arguments: {"token": _token, "staff_flag": _isStaff},
              );
            },
            child: Text('Stok Güncelle'),
          ),
          SizedBox(height: 8),

          // Kullanıcı Stoklarını Gör
          ElevatedButton(
            onPressed: () {
              Navigator.pushNamed(
                context,
                '/admin_user_stocks',
                arguments: {"token": _token, "staff_flag": _isStaff},
              );
            },
            child: Text('Kullanıcı Stoklarını Gör'),
          ),
        ],
      ),
    );
  }
}
