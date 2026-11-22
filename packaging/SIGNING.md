# Signing the standalone apps

The release zips are not signed, so macOS Gatekeeper and Windows
SmartScreen ask for confirmation on first launch (the README explains
how). Signing removes that prompt. It requires paid certificates and is
therefore not part of the build; the procedure below adds it to a
finished build.

## macOS: Developer ID signature and notarization

Requirements: an Apple Developer Program membership, a *Developer ID
Application* certificate in the login keychain, and Xcode's command
line tools. The notarization credentials are stored once:

```bash
xcrun notarytool store-credentials visolab \
  --apple-id "<apple id>" --team-id "<TEAMID>" --password "<app-specific password>"
```

The following entitlements are saved as `entitlements.plist` (a PyInstaller app
under the hardened runtime needs them to load its bundled Python):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>com.apple.security.cs.allow-unsigned-executable-memory</key><true/>
  <key>com.apple.security.cs.disable-library-validation</key><true/>
</dict></plist>
```

Each zip written by `build_macos.sh` is then signed (Apple Silicon and
Intel):

```bash
ZIP="dist/macOS/OptoDrum Connector-macOS-Apple-Silicon.zip"
ID="Developer ID Application: <Name> (<TEAMID>)"
rm -rf sign && mkdir sign && ditto -x -k "$ZIP" sign/
codesign --force --deep --options runtime --timestamp \
  --entitlements entitlements.plist --sign "$ID" "sign/OptoDrum Connector.app"
codesign --verify --deep --strict --verbose=2 "sign/OptoDrum Connector.app"
ditto -c -k --keepParent "sign/OptoDrum Connector.app" sign/notarize.zip
xcrun notarytool submit sign/notarize.zip --keychain-profile visolab --wait
xcrun stapler staple "sign/OptoDrum Connector.app"
spctl --assess --type execute --verbose "sign/OptoDrum Connector.app"   # "accepted, source=Notarized Developer ID"
rm -f "$ZIP" && ditto -c -k --sequesterRsrc --keepParent "sign/OptoDrum Connector.app" "$ZIP"
```

The signed app is run once (or `"sign/OptoDrum Connector.app/Contents/MacOS/OptoDrum Connector"
--selftest`) before publication: a missing entitlement appears as a
crash at start, not at signing time. If notarization is rejected,
`xcrun notarytool log <submission id> --keychain-profile visolab`
names the file at fault.

## Windows: Authenticode signature

Requirements: a code signing certificate (an OV or EV certificate from
a certificate authority, or Azure Trusted Signing) and `signtool.exe`
from the Windows SDK. After `build_windows.bat`, the archive
`dist\Windows\OptoDrum Connector-Windows.zip` is unpacked, the executable is signed and the
folder is compressed again:

```bat
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /a "OptoDrum Connector\OptoDrum Connector.exe"
signtool verify /pa /v "OptoDrum Connector\OptoDrum Connector.exe"
```

`/a` selects the certificate from the store; `/f cert.pfx /p
<password>` selects a file, and the Trusted Signing `dlib` options
select Azure. SmartScreen may still warn until the certificate has built up
download reputation.
