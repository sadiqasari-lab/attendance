# Inspire Attendance System — Development Plan

## Project Overview
Production-ready, enterprise-grade, modular, multi-tenant Attendance Management System
for Arab Inspire Company (Riyadh) and its tenants.

**Domain:** arabinspire.cloud
**Routing:** Path-based `/{tenant_slug}/...`
**Architecture:** Modular Multi-Tenant SaaS

---

## Phase 1: Backend Foundation
### Milestone 1.1 — Project Infrastructure
- [√] Docker Compose setup (PostgreSQL, Redis, Celery, Nginx, Gunicorn)
- [√] Django project scaffolding with modular app structure
- [√] Settings management (base, development, staging, production)
- [√] Environment variable configuration (.env)

### Milestone 1.2 — Core Framework
- [√] Base abstract models (UUID, tenant, timestamps, soft-delete, audit)
- [√] Tenant middleware (path-based routing, tenant isolation)
- [√] RBAC permission system
- [√] JWT authentication (access + refresh tokens)
- [√] Custom user model with employee profile
- [√] Audit logging framework

### Milestone 1.3 — Tenant & Account Management
- [√] Group / Tenant / Department models
- [√] Employee model with multi-tenant assignment
- [√] Admin-configurable tenant slugs
- [√] Tenant isolation at queryset level
- [√] User registration and management APIs

### Milestone 1.4 — Attendance Engine
- [√] Shift / AttendancePolicy / Geofence / WifiPolicy models
- [√] AttendanceRecord model with full validation fields
- [√] Server-side validation engine (12-point check)
- [√] Offline attendance handling (one per shift, replay protection)
- [√] Duplicate prevention
- [√] Clock tampering detection
- [√] Attendance correction request workflow

### Milestone 1.5 — Biometric System
- [√] BiometricTemplate model (AES-256 encrypted embeddings)
- [√] Self-enrollment flow (multi-angle capture)
- [√] face_recognition (dlib) integration
- [√] Liveness detection service
- [√] Embedding comparison service
- [√] Enrollment audit logging

### Milestone 1.6 — Projects & Approvals
- [√] Project model with geofence association
- [√] EmployeeProjectAssignment model
- [√] Approval workflow for corrections
- [√] Approval notification system

### Milestone 1.7 — Devices & Security
- [√] DeviceRegistry model
- [√] Device binding logic (company + BYOD)
- [√] Root/jailbreak detection endpoint
- [√] One-device-per-user enforcement
- [√] Device change approval workflow

### Milestone 1.8 — Integration (HRIS)
- [√] Webhook configuration model
- [√] Push webhook delivery (attendance events)
- [√] Pull API endpoints (logs, shifts, summaries)
- [√] Token + IP allowlist authentication
- [√] Rate limiting
- [√] Integration audit logging

### Milestone 1.9 — Real-Time Features
- [√] Django Channels WebSocket setup
- [√] Live attendance map consumer
- [√] Role-based visibility filtering
- [√] Map clustering data endpoint

### Milestone 1.10 — Testing
- [√] Unit tests for all models
- [√] Tenant isolation tests
- [√] Attendance validation tests
- [√] Biometric service tests
- [√] API endpoint tests
- [√] Permission/RBAC tests
- [√] Load testing (500 concurrent users) — Locust scenarios
- Target: 85%+ coverage

---

## Phase 2: Web Frontend
### Milestone 2.1 — React Project Setup
- [√] Vite + React 19 + TypeScript project scaffold
- [√] Tailwind CSS with dark mode + RTL Arabic support
- [√] i18next with English + Arabic translations
- [√] Zustand state management (auth + theme stores)
- [√] Central API client with JWT auto-refresh
- [√] Protected routes with RBAC role gating

### Milestone 2.2 — Dashboard & Admin
- [√] Dashboard module (stat cards, Chart.js doughnut + bar charts, summary table)
- [√] Admin modules: Employees, Shifts, Geofences, Devices management
- [√] Settings module (profile, theme/language toggle, password change)

### Milestone 2.3 — Attendance & Map
- [√] Attendance records module (filterable table with date/status filters)
- [√] Real-time attendance map (WebSocket, Leaflet markers, event stream)

---

## Phase 3: Mobile App
### Milestone 3.1 — React Native Setup
- [√] TypeScript project scaffolding (React Native 0.76.6 + React 19)
- [√] Clean architecture with service layer
- [√] Secure storage abstraction (EncryptedStorage)
- [√] Central API client with JWT auto-refresh + queue

### Milestone 3.2 — Core Features
- [√] Auth module (login screen, token management, Zustand store)
- [√] Attendance module (dashboard, clock-in/out, history, offline fallback)
- [√] Camera module (selfie capture with front camera)
- [√] Biometric enrollment module (multi-angle capture, enrollment API)

### Milestone 3.3 — Security & Offline
- [√] Device security module (root detection, device binding, registration)
- [√] Offline sync module (encrypted queue, auto-sync on reconnect, replay protection)
- [√] GPS location hook with permission handling

### Milestone 3.4 — Production Builds
- [√] Android: Release signing, ProGuard, min SDK 24, .aab bundle config, network security
- [√] iOS: Podfile, Info.plist permissions, App Transport Security, AppDelegate

---

## Security Checklist
- [√] JWT with short-lived access tokens
- [√] RBAC at API level
- [√] Tenant data isolation
- [√] AES-256 biometric encryption
- [√] CSRF/XSS protection
- [√] Rate limiting
- [√] Audit logging
- [√] Input validation
- [√] SQL injection prevention (Django ORM)
- [ ] SSL/TLS (Let's Encrypt) — deployment phase
- [ ] Security headers (CSP, HSTS) — deployment phase

## Deployment Checklist
- [√] Docker Compose configuration
- [√] Nginx reverse proxy config
- [√] Gunicorn worker config
- [√] Redis for caching + Celery broker
- [√] Celery worker + beat configuration
- [ ] SSL certificate setup
- [ ] Backup cron job configuration
- [ ] Monitoring setup
- [ ] CI/CD pipeline

## Integration Roadmap
- [√] HRIS push webhooks
- [√] HRIS pull endpoints
- [ ] Play Integrity API (future mobile)
- [ ] SSO/SAML integration (future)
- [ ] Payroll system integration (excluded from scope)
