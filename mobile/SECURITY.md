# Mobile Security Notes (Android)

## What is hardened
- `release` build blocks cleartext HTTP (`usesCleartextTraffic=false`).
- `release` build disables local backups (`allowBackup=false`).
- `release` enables R8/ProGuard (`isMinifyEnabled=true`, `isShrinkResources=true`).
- Network security config enforces TLS in production builds.

## Build variants
- `debug`: keeps cleartext enabled for local development (`http://10.0.2.2:8000`).
- `release`: HTTPS-only, optimized and obfuscated.

## Recommended release checklist
1. Set API base URL to HTTPS endpoint.
2. Sign with dedicated release keystore (not debug key).
3. Run:
```bash
cd mobile/ConsultorioDentalRC
./gradlew clean lint assembleRelease
```
4. Verify APK does not call HTTP endpoints.
5. Upload only signed release artifacts.
