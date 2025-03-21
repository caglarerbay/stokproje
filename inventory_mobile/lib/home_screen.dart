import 'package:flutter/material.dart';

class HomeScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Ana Ekran')),
      body: Center(
        child: Text('Hoş geldiniz!', style: TextStyle(fontSize: 20)),
      ),
    );
  }
}
