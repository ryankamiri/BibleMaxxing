# Components Guide

This folder owns reusable UI components.

- Components should be presentation-focused and receive behavior through closures or bindings.
- YouTube playback must use the official embedded player through `WKWebView`,
  loaded from the backend player shell URL rather than inline local HTML.
- Do not add video byte download, offline playback, or camera-roll save behavior.
