# BibleMaxxing

BibleMaxxing is a native SwiftUI iOS prototype backed by a FastAPI/Postgres
service at `https://api.tailortom.org/biblemaxxing`.

## Quick Local Check

The iOS app uses the hosted API by default, which is the fastest way to test on
Ryan's iPhone from anywhere.

```bash
./scripts/build_ios_simulator.sh
open ios/BibleMaxxing.xcodeproj
```

## Local Backend

Use this when you want a local API on your Mac. It uses SQLite by default and
does not need production secrets.

```bash
./scripts/dev_backend.sh setup
./scripts/dev_backend.sh run
```

In another terminal:

```bash
./scripts/dev_backend.sh smoke
```

Local API:

- Health: `http://127.0.0.1:8000/biblemaxxing/health`
- Docs: `http://127.0.0.1:8000/biblemaxxing/docs`

## Install On Ryan's iPhone Only

You do not need TestFlight or App Store distribution for a personal device
build. Open the Xcode project, select Ryan's connected iPhone as the run
destination, choose Ryan's Personal Team in Signing & Capabilities, and press
Run.

The app target is configured as iPhone-only with bundle ID:

```text
com.ryanamiri.biblemaxxing
```

Keep using the hosted API while testing on-device unless you deliberately want
to expose your Mac's local backend to the phone.
