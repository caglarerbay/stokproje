import 'package:flutter/material.dart';
// Senin register_screen.dart dosyanı import et
import 'screens/register_screen.dart';
// Az önce oluşturduğun login_screen.dart dosyasını import et
import 'screens/login_screen.dart';
// Eğer forgot_password_screen.dart varsa import et
import 'screens/forgot_password_screen.dart';
// Eğer home_screen.dart varsa import et
import 'screens/home_screen.dart';
import 'screens/transfer_usage_screen.dart';
import 'screens/admin_panel_screen.dart';
import 'screens/admin_add_product_screen.dart';
import 'screens/admin_update_stock_screen.dart';
import 'screens/admin_user_stocks_screen.dart';
import 'screens/my_stock_screen.dart';
import 'screens/admin_settings_screen.dart';

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
        '/admin_panel': (context) => AdminPanelScreen(),
        '/admin_add_product': (context) => AdminAddProductScreen(),
        '/admin_update_stock': (context) => AdminUpdateStockScreen(),
        '/admin_user_stocks': (context) => AdminUserStocksScreen(),
        '/my_stock_screen': (context) => MyStockScreen(),
        '/admin_settings': (context) => AdminSettingsScreen(),
      },
      // Eğer “/home” gibi bir ekrana gideceksen, oraya da widget eklemen lazım
      // Bu satırlar senin diğer dosyalarında tanımlı widget'lara işaret etmeli
    );
  }
}
