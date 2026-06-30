# Xcode Project Agent Guide

This folder contains Xcode project metadata for the BibleMaxxing iOS app.

- Keep this package limited to project configuration and shared schemes.
- Do not store secrets, provisioning profiles, signing certificates, or user-specific Xcode state here.
- Keep app source code under `ios/BibleMaxxingApp/`.
- Prefer build settings that work for simulator builds without requiring Ryan's Apple Developer account.
- `project.pbxproj` is intentionally versioned. For this personal sideloaded
  prototype, Ryan's Apple development team ID can live in the project file so
  agents can install onto his phone. Do not gitignore the project file.
