import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'services/api_service.dart';
import 'services/auth_service.dart';
import 'services/attendance_service.dart';
import 'services/leave_service.dart';
import 'services/payslip_service.dart';
import 'utils/app_theme.dart';
import 'utils/app_router.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Lock to portrait
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // System UI
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.dark,
  ));

  final prefs = await SharedPreferences.getInstance();

  runApp(
    MultiProvider(
      providers: [
        Provider<SharedPreferences>.value(value: prefs),
        Provider<ApiService>(create: (_) => ApiService()),
        ChangeNotifierProxyProvider<ApiService, AuthService>(
          create: (ctx) => AuthService(ctx.read<ApiService>(), prefs),
          update: (ctx, api, prev) => prev ?? AuthService(api, prefs),
        ),
        ChangeNotifierProxyProvider<ApiService, AttendanceService>(
          create: (ctx) => AttendanceService(ctx.read<ApiService>()),
          update: (ctx, api, prev) => prev ?? AttendanceService(api),
        ),
        ChangeNotifierProxyProvider<ApiService, LeaveService>(
          create: (ctx) => LeaveService(ctx.read<ApiService>()),
          update: (ctx, api, prev) => prev ?? LeaveService(api),
        ),
        ChangeNotifierProxyProvider<ApiService, PayslipService>(
          create: (ctx) => PayslipService(ctx.read<ApiService>()),
          update: (ctx, api, prev) => prev ?? PayslipService(api),
        ),
      ],
      child: const WorkSphereApp(),
    ),
  );
}

class WorkSphereApp extends StatelessWidget {
  const WorkSphereApp({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthService>(
      builder: (context, auth, _) {
        return MaterialApp.router(
          title: 'WorkSphere HR',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.lightTheme,
          darkTheme: AppTheme.darkTheme,
          themeMode: ThemeMode.system,
          routerConfig: AppRouter.router(auth),
        );
      },
    );
  }
}
