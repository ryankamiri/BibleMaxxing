# Components Guide

This folder owns reusable UI components.

- Components should be presentation-focused and receive behavior through closures or bindings.
- YouTube playback must use the official embedded player through `WKWebView`,
  loaded from the backend player shell URL rather than inline local HTML.
- Keep embedded player web views non-interactive; feed gestures, taps, and
  controls belong to SwiftUI so native YouTube chrome does not steal touches.
- Do not add video byte download, offline playback, or camera-roll save behavior.
- Use `BrandLogoView` for in-app logo placement so the approved asset is sized
  and rounded consistently across launch, auth, and feed chrome surfaces.
