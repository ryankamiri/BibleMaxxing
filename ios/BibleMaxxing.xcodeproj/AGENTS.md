# Xcode Project Agent Guide

This folder contains Xcode project metadata for the BibleMaxxing iOS app.

- Keep this package limited to project configuration and shared schemes.
- Do not store secrets, provisioning profiles, signing certificates, or user-specific Xcode state here.
- Keep app source code under `ios/BibleMaxxingApp/`.
- Prefer build settings that work for simulator builds without requiring Ryan's Apple Developer account.
