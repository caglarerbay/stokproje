import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../services/api_constants.dart';

class AdminSettingsScreen extends StatefulWidget {
  @override
  _AdminSettingsScreenState createState() => _AdminSettingsScreenState();
}

class _AdminSettingsScreenState extends State<AdminSettingsScreen> {
  String? _token;
  bool _isStaff = false;

  final _criticalEmailController = TextEditingController();
  final _exportEmailController = TextEditingController();
  String? _dailyAccessCode;

  String? _errorMessage;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      final args = ModalRoute.of(context)?.settings.arguments;
      if (args is Map) {
        _token = args["token"];
        _isStaff = args["staff_flag"] ?? false;

        // Ayarları çek
        _fetchAppSettings();
      } else {
        setState(() {
          _errorMessage = "AdminSettings: Token/staff_flag yok.";
        });
      }
    });
  }

  @override
  void dispose() {
    _criticalEmailController.dispose();
    _exportEmailController.dispose();
    super.dispose();
  }

  Future<void> _fetchAppSettings() async {
    if (_token == null || _token!.isEmpty) return;
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final url = Uri.parse(
      '${ApiConstants.baseUrl}/api/admin_get_app_settings/',
    );
    final headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Token $_token',
    };

    try {
      final response = await http.get(url, headers: headers);
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _criticalEmailController.text = data["critical_stock_email"] ?? "";
          _exportEmailController.text = data["export_stock_email"] ?? "";
          _dailyAccessCode = data["daily_code"] ?? "";
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage = "Ayarları çekerken hata: ${response.statusCode}";
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Sunucuya erişilemedi (fetchAppSettings): $e";
        _isLoading = false;
      });
    }
  }

  Future<void> _updateAppSettings() async {
    if (_token == null || _token!.isEmpty) {
      setState(() {
        _errorMessage = "Token yok, ayar güncellenemiyor.";
      });
      return;
    }
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final url = Uri.parse(
      '${ApiConstants.baseUrl}/api/admin_update_app_settings/',
    );
    final headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Token $_token',
    };
    final body = {
      "critical_stock_email": _criticalEmailController.text.trim(),
      "export_stock_email": _exportEmailController.text.trim(),
    };

    try {
      final response = await http.post(
        url,
        headers: headers,
        body: json.encode(body),
      );
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _errorMessage = data["detail"] ?? "Ayarlar güncellendi.";
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage = "Ayar güncelleme hatası: ${response.statusCode}";
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Sunucuya erişilemedi (updateAppSettings): $e";
        _isLoading = false;
      });
    }
  }

  Future<void> _generateDailyCode() async {
    if (_token == null || _token!.isEmpty) {
      setState(() {
        _errorMessage = "Token yok, günlük kod üretilemez.";
      });
      return;
    }
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final url = Uri.parse(
      '${ApiConstants.baseUrl}/api/admin_generate_daily_code/',
    );
    final headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Token $_token',
    };

    try {
      final response = await http.post(url, headers: headers);
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _dailyAccessCode = data["daily_code"] ?? "";
          _errorMessage = data["detail"] ?? "Kod üretildi.";
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage = "Kod üretirken hata: ${response.statusCode}";
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Sunucuya erişilemedi (generateDailyCode): $e";
        _isLoading = false;
      });
    }
  }

  Future<void> _sendCriticalStockMail() async {
    if (_token == null || _token!.isEmpty) {
      setState(() {
        _errorMessage = "Token yok, kritik stok maili gönderilemez.";
      });
      return;
    }
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final url = Uri.parse(
      '${ApiConstants.baseUrl}/api/send_excel_report_email_api/',
    );
    final headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Token $_token',
    };

    try {
      final response = await http.post(url, headers: headers);
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _errorMessage = data["detail"] ?? "Mail gönderildi.";
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage = "Kritik stok mailinde hata: ${response.statusCode}";
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Sunucuya erişilemedi (sendCriticalStockMail): $e";
        _isLoading = false;
      });
    }
  }

  Future<void> _sendFullStockMail() async {
    if (_token == null || _token!.isEmpty) {
      setState(() {
        _errorMessage = "Token yok, tüm stok raporu gönderilemez.";
      });
      return;
    }
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final url = Uri.parse(
      '${ApiConstants.baseUrl}/api/send_full_stock_report/',
    );
    final headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Token $_token',
    };

    try {
      final response = await http.post(url, headers: headers);
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _errorMessage = data["detail"] ?? "Mail gönderildi.";
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage = "Tüm stok mailinde hata: ${response.statusCode}";
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Sunucuya erişilemedi (sendFullStockMail): $e";
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Admin Ayarları')),
      body:
          _isLoading
              ? Center(child: CircularProgressIndicator())
              : ListView(
                padding: EdgeInsets.all(16),
                children: [
                  if (_errorMessage != null && _errorMessage!.isNotEmpty)
                    Text(_errorMessage!, style: TextStyle(color: Colors.red)),
                  SizedBox(height: 16),

                  Text(
                    'Ayarlar',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 8),

                  // Kritik Stok Mail Adresi
                  TextField(
                    controller: _criticalEmailController,
                    decoration: InputDecoration(
                      labelText: 'Kritik Stok Mail Adresi',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  SizedBox(height: 8),

                  // Dışa Aktarım Mail Adresi
                  TextField(
                    controller: _exportEmailController,
                    decoration: InputDecoration(
                      labelText: 'Dışa Aktarım Mail Adresi',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  SizedBox(height: 8),

                  ElevatedButton(
                    onPressed: _updateAppSettings,
                    child: Text('Ayarları Kaydet'),
                  ),

                  SizedBox(height: 16),
                  Text(
                    'Daily Access Code: ${_dailyAccessCode ?? "Henüz oluşturulmadı"}',
                    style: TextStyle(fontSize: 16),
                  ),
                  SizedBox(height: 8),
                  ElevatedButton(
                    onPressed: _generateDailyCode,
                    child: Text('Yeni Günlük Kod Oluştur'),
                  ),

                  SizedBox(height: 16),
                  Text(
                    'Mail Gönder',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 8),

                  // Kritik Stok Maili Gönder
                  ElevatedButton(
                    onPressed: _sendCriticalStockMail,
                    child: Text('Kritik Stok Maili Gönder'),
                  ),
                  SizedBox(height: 8),

                  // Tüm Stok Raporu Gönder
                  ElevatedButton(
                    onPressed: _sendFullStockMail,
                    child: Text('Tüm Stok Raporu Gönder'),
                  ),
                ],
              ),
    );
  }
}
