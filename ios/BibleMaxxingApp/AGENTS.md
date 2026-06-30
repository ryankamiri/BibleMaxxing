# BibleMaxxing App Source Guide

This folder contains source code for the native SwiftUI iOS app.

- Keep app code SwiftUI-first and dark-mode only.
- Keep backend calls behind `Services/APIClient.swift`.
- Keep decoded request and response shapes in `Models/APIModels.swift`.
- Use YouTube official embedded playback only, routed through the backend player
  shell URL from `Services/APIClient.swift`; never add MP4 download, cache,
  rehost, or camera-roll save logic.
- Keep auth, onboarding, feed, and account deletion flows runnable without hardcoded secrets.
- Keep `Assets.xcassets/AppIcon.appiconset` and `Assets.xcassets/BrandLogo.imageset`
  in sync when the approved BibleMaxxing logo changes.
