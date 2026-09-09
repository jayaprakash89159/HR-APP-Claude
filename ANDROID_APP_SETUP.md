# WorkSphere HR Android App Setup Guide

This guide explains the complete process used to prepare and start the WorkSphere HR Flutter mobile application on Windows.

## 1. Project Locations

Backend project:

```text
D:\HR APP CLaude\worksphere_complete_fixed\worksphere_app
```

Flutter project:

```text
D:\HR APP CLaude\worksphere_complete_fixed\worksphere_app\mobile
```

All commands in this guide are intended for PowerShell inside VS Code.

## 2. Install Git

Git is required to download the Flutter SDK.

Check whether Git is already installed:

```powershell
git --version
```

If Git is not installed, run PowerShell as Administrator and use:

```powershell
winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements
```

If `winget` reports that Git is already installed but tries to upgrade it, use the existing installation. In this setup Git was located at:

```text
C:\Program Files\Git\cmd\git.exe
```

## 3. Install Flutter SDK

Flutter was installed under `C:\src\flutter`.

The direct ZIP download stalled, so the Flutter stable repository was downloaded using Git instead:

```powershell
New-Item -ItemType Directory -Force -Path C:\src | Out-Null

& 'C:\Program Files\Git\cmd\git.exe' clone --depth 1 --branch stable https://github.com/flutter/flutter.git C:\src\flutter
```

Add Flutter to the user PATH:

```powershell
[Environment]::SetEnvironmentVariable(
  'Path',
  [Environment]::GetEnvironmentVariable('Path', 'User') + ';C:\src\flutter\bin',
  'User'
)
```

For the current terminal session, use:

```powershell
$env:Path = 'C:\src\flutter\bin;C:\Program Files\Git\cmd;' + $env:Path
```

Verify Flutter:

```powershell
flutter --version
```

Expected result is a stable Flutter version and a Dart version. This setup used Flutter `3.47.2` and Dart `3.13.2`.

## 4. Install Android Studio

Android Studio provides the Android SDK, emulator, and Android build tools.

Install it from the VS Code terminal:

```powershell
winget install --id Google.AndroidStudio -e --source winget --accept-source-agreements --accept-package-agreements
```

The installer may request Administrator permission. Allow the installer to complete.

Open Android Studio after installation and complete the first-run setup. Install these components when prompted:

- Android SDK
- Android SDK Platform
- Android SDK Build-Tools
- Android SDK Command-line Tools
- Android Emulator

Then accept Android licenses:

```powershell
flutter doctor --android-licenses
```

Answer `y` to each license prompt.

Check the complete environment:

```powershell
flutter doctor
```

The Android toolchain should show a check mark. The Visual Studio warning can be ignored unless Windows desktop builds are required.

If Flutter cannot find the SDK, configure its location explicitly. The usual location is:

```powershell
flutter config --android-sdk "$env:LOCALAPPDATA\Android\Sdk"
```

## 5. Generate the Android Runner

The repository originally contained Flutter Dart code but did not contain the generated Android platform folder.

Go to the mobile project:

```powershell
cd "D:\HR APP CLaude\worksphere_complete_fixed\worksphere_app\mobile"
```

Generate Android files:

```powershell
flutter create --platforms=android .
```

This creates the `android` folder, Gradle files, Android manifest files, launcher resources, and the Android activity.

## 6. Generate Web Support for Laptop Preview

To run the mobile UI in Chrome on the laptop, generate web support:

```powershell
flutter create --platforms=web .
```

This creates the `web` folder.

Chrome preview is useful for checking screens, navigation, login layout, leave pages, and attendance pages. Camera, GPS, and Android-specific features should be tested on Android.

## 7. Install Flutter Packages

From the `mobile` directory:

```powershell
flutter pub get
```

The project uses packages for:

- HTTP and API communication
- JWT token storage
- GPS and geocoding
- Camera and selfies
- Navigation
- Leave and attendance screens
- Local notifications
- Firebase integrations

Some packages report that newer versions are available. These are informational messages and do not prevent the current dependency set from working.

The `open_file` package reports a macOS default-plugin warning. This does not block Android or web compilation.

## 8. Fix Missing Asset References

The original `pubspec.yaml` referenced asset folders and font files that were not present:

```text
assets/images/
assets/icons/
assets/lottie/
assets/fonts/
assets/fonts/PlusJakartaSans-Regular.ttf
```

Those stale declarations were removed from `mobile/pubspec.yaml` so Flutter could compile the existing application.

If custom font files are added later, they can be declared again after the actual files exist.

## 9. Fix Flutter 3.47 Compatibility Issues

Flutter 3.47 requires `CardThemeData` in the `ThemeData.cardTheme` property. The project theme was updated from:

```dart
CardTheme(...)
```

to:

```dart
CardThemeData(...)
```

The project had two `LeaveBalanceCard` classes. The old static placeholder version in `stat_card.dart` was removed, leaving the API-backed version in:

```text
mobile/lib/widgets/leave_balance_card.dart
```

The autogenerated counter test was replaced with a WorkSphere API configuration smoke test because the project uses `WorkSphereApp`, not the Flutter template class `MyApp`.

## 10. Validate the Flutter Project

Run static analysis:

```powershell
flutter analyze
```

The current project has no analyzer errors. It may display informational warnings about deprecated APIs, unused imports, and suggestions such as adding `const`.

Run tests:

```powershell
flutter test
```

The current smoke test should pass.

## 11. Configure the API URL

The mobile app reads the backend URL from the `API_BASE_URL` build variable.

The default value is:

```text
http://10.0.2.2:8000
```

`10.0.2.2` means the host computer when the app runs inside an Android emulator.

For Chrome on the laptop:

```powershell
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
```

For an Android emulator:

```powershell
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

For a physical Android phone connected to the same Wi-Fi network, find the computer IP with:

```powershell
ipconfig
```

Then run, replacing the example IP:

```powershell
flutter run --dart-define=API_BASE_URL=http://192.168.1.25:8000
```

The computer IP must be included in Django `ALLOWED_HOSTS`, and Windows Firewall must allow the selected port.

## 12. Start the Backend with Docker

The backend needs Django, PostgreSQL, Redis, Celery, and Nginx.

From the repository root, build the images:

```powershell
cd "D:\HR APP CLaude\worksphere_complete_fixed\worksphere_app"
docker compose build
```

The build creates the `worksphere_hr_app:latest` image used by Django and Celery services.

Start the standard stack:

```powershell
docker compose up -d
```

## 13. Local Docker Port Override

On this computer, another project was already using PostgreSQL port `5432`, Redis port `6379`, and an application port. A local override file was created:

```text
docker-compose.local.yml
```

It provides alternate host ports:

| Service | Local port |
|---|---:|
| WorkSphere Nginx | 8080 |
| PostgreSQL | 55432 |
| Redis | 56379 |
| Flower | 5556 |

Start WorkSphere without stopping the other Docker project:

```powershell
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
```

Check service status:

```powershell
docker compose -f docker-compose.yml -f docker-compose.local.yml ps
```

Django runs migrations, collects static files, creates demo data, and starts Gunicorn automatically.

Check the web health endpoint:

```powershell
Invoke-WebRequest http://localhost:8080/health/ -UseBasicParsing
```

Open the API documentation:

```text
http://localhost:8080/api/docs/
```

Depending on the active port mappings, `http://localhost:8000` may also work.

## 14. Demo Login Accounts

The Docker startup creates demo accounts:

| Role | Email | Password |
|---|---|---|
| Super Admin | admin@worksphere.hr | Admin@123 |
| HR Admin | hr@worksphere.hr | Admin@123 |
| Manager | manager@worksphere.hr | Mgr@123 |
| Employee | employee@worksphere.hr | Emp@123 |
| Payroll | payroll@worksphere.hr | Pay@123 |

Use the Employee account to test clock-in, clock-out, attendance history, leave applications, balances, and holidays.

## 15. Run the App on the Laptop

Start Chrome preview after Docker is running:

```powershell
cd "D:\HR APP CLaude\worksphere_complete_fixed\worksphere_app\mobile"
& 'C:\src\flutter\bin\flutter.bat' run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
```

If the backend is only available through local Nginx port `8080`, use:

```powershell
& 'C:\src\flutter\bin\flutter.bat' run -d chrome --dart-define=API_BASE_URL=http://localhost:8080
```

The Chrome window will show:

- WorkSphere login screen
- Home dashboard
- Attendance clock card
- Attendance history
- Leave balances
- Leave application form
- Leave application status
- Holiday calendar
- Profile and payslip navigation

## 16. Run on an Android Emulator

List available emulators:

```powershell
flutter emulators
```

Launch an emulator:

```powershell
flutter emulators --launch <emulator_id>
```

Verify devices:

```powershell
flutter devices
```

Run the app:

```powershell
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

When Android Studio has finished SDK setup, `flutter doctor` should show the Android toolchain and the emulator should appear in `flutter devices`.

## 17. Build the APK

For a debug APK:

```powershell
cd "D:\HR APP CLaude\worksphere_complete_fixed\worksphere_app\mobile"
flutter build apk --debug --dart-define=API_BASE_URL=https://your-domain.com
```

For a release APK:

```powershell
flutter build apk --release --dart-define=API_BASE_URL=https://your-domain.com
```

The release APK is created at:

```text
mobile\build\app\outputs\flutter-apk\app-release.apk
```

To install the debug APK on a connected device:

```powershell
flutter install
```

## 18. Important Troubleshooting

### Flutter command is not recognized

Use the full path:

```powershell
& 'C:\src\flutter\bin\flutter.bat' doctor
```

Or close and reopen VS Code after adding Flutter to PATH.

### Android SDK not found

Open Android Studio, complete first-run setup, install the Android SDK and command-line tools, then run:

```powershell
flutter config --android-sdk "$env:LOCALAPPDATA\Android\Sdk"
flutter doctor --android-licenses
flutter doctor
```

### Docker port is already allocated

Use the local override:

```powershell
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
```

Do not stop unrelated containers unless you are sure they are not needed.

### Chrome debug service timeout

Try running Chrome preview again after closing old Flutter/Chrome debug sessions:

```powershell
& 'C:\src\flutter\bin\flutter.bat' clean
& 'C:\src\flutter\bin\flutter.bat' pub get
& 'C:\src\flutter\bin\flutter.bat' run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
```

A Chrome debug timeout does not necessarily mean the application code failed. `flutter analyze` and `flutter test` are the first checks to run.

### Login does not work

Confirm that the WorkSphere API, not another application, is running on the configured port:

```powershell
Invoke-WebRequest http://localhost:8000/api/docs/ -UseBasicParsing
```

The page should identify the WorkSphere HR API. If Nginx is on port `8080`, use `http://localhost:8080` in `API_BASE_URL`.

## 19. Recommended Daily Start Sequence

Backend terminal:

```powershell
cd "D:\HR APP CLaude\worksphere_complete_fixed\worksphere_app"
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
```

Mobile terminal:

```powershell
cd "D:\HR APP CLaude\worksphere_complete_fixed\worksphere_app\mobile"
& 'C:\src\flutter\bin\flutter.bat' run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
```

For Android emulator instead of Chrome:

```powershell
& 'C:\src\flutter\bin\flutter.bat' run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

## 20. Final Expected Result

When everything is installed and running:

1. Docker containers show `Up` or `Healthy`.
2. `http://localhost:8000/api/docs/` or `http://localhost:8080/api/docs/` opens Swagger documentation.
3. Chrome or the Android emulator opens the WorkSphere login screen.
4. The employee demo account can log in.
5. Attendance, leave, balances, and holiday data are loaded from the same Django database through the REST API.
6. A release APK can be generated with `flutter build apk --release`.
