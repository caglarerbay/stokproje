import 'package:flutter/material.dart';
// Senin register_screen.dart dosyanı import et
import 'register_screen.dart';
// Az önce oluşturduğun login_screen.dart dosyasını import et
import 'login_screen.dart';
// Eğer forgot_password_screen.dart varsa import et
import 'forgot_password_screen.dart';
// Eğer home_screen.dart varsa import et
import 'home_screen.dart';
import 'transfer_usage_screen.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Inventory Mobile',
      // Uygulama açıldığında ilk açılacak route (LoginScreen)
      initialRoute: '/login',
      routes: {
        '/login': (context) => LoginScreen(),
        '/register': (context) => RegisterScreen(),
        '/forgot_password': (context) => ForgotPasswordScreen(),
        '/home': (context) => HomeScreen(),
        '/transfer_usage': (context) => TransferUsageScreen(),
      },
      // Eğer “/home” gibi bir ekrana gideceksen, oraya da widget eklemen lazım
      // Bu satırlar senin diğer dosyalarında tanımlı widget'lara işaret etmeli
    );
  }
}
