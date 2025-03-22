import 'package:flutter/material.dart';

class AdminPanelScreen extends StatefulWidget {
  @override
  _AdminPanelScreenState createState() => _AdminPanelScreenState();
}

class _AdminPanelScreenState extends State<AdminPanelScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Admin Paneli')),
      body: ListView(
        padding: EdgeInsets.all(16),
        children: [
          Text(
            'Hoş geldin, Admin!',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          SizedBox(height: 16),

          ElevatedButton(
            onPressed: () {
              Navigator.pushNamed(context, '/admin_add_product');
            },
            child: Text('Ürün Ekle'),
          ),
          SizedBox(height: 8),

          ElevatedButton(
            onPressed: () {
              // Henüz endpoint yok, placeholder
              Navigator.pushNamed(context, '/admin_update_stock');
            },
            child: Text('Stok Güncelle'),
          ),
          SizedBox(height: 8),

          ElevatedButton(
            onPressed: () {
              // Henüz endpoint yok, placeholder
              Navigator.pushNamed(context, '/admin_user_stocks');
            },
            child: Text('Kullanıcı Stoklarını Gör'),
          ),
        ],
      ),
    );
  }
}
