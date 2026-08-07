# ThinkFive Mobile App

The Flutter mobile application for the ThinkFive AI Banking platform.

## Architecture
- **State Management**: `flutter_bloc`
- **Routing**: `go_router`
- **Networking**: `dio` with cookie persistence via `flutter_secure_storage`
- **Dependency Injection**: Simple Service Locator (`Dependencies` class)
- **Data Models**: Clean Domain Entities / DTOs using Equatable

## Setup and Run
Use `--dart-define=USE_FIXTURES=true` to run against simulated data without requiring the backend:

```bash
flutter run --dart-define=USE_FIXTURES=true
```

## Role Based Authentication (Fixtures)
When running with fixtures, the role is determined by the email address:
- `analyst@thinkfive.com` -> Analyst View
- `supervisor@thinkfive.com` -> Supervisor View
- `admin@thinkfive.com` -> Admin View
- Any other email (e.g. `priya@thinkfive.com`) -> Customer View

## Features Implemented
- Authentication (Login, Logout, Session persistence via cookies)
- Customer Dashboard (Balances, Transactions, Cases, Alerts)
- AI Chat (SSE integration using custom `SseClient` and `SseParser`)
- Analyst Approvals Queue
- Supervisor Metrics Dashboard
