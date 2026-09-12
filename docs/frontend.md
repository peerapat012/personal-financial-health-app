# Frontend & UI Guidelines

## 1. Overview

The desktop application uses **Tauri 2 + React + TypeScript + Vite**.

The UI is designed primarily for desktop usage and should follow desktop dashboard patterns rather than mobile-first patterns.

The frontend should remain simple, maintainable, and suitable for a single-developer project.

Primary frontend stack:

```text
Tauri 2
│
├── React
├── TypeScript
├── Vite
│
├── Styling & UI
│   ├── Tailwind CSS
│   ├── shadcn/ui
│   └── Lucide React
│
├── Data Visualization
│   └── Recharts
│
├── Forms
│   ├── React Hook Form
│   └── Zod
│
├── Server State
│   └── TanStack Query
│
└── Client State
    └── Zustand (only when necessary)
```

---

# 2. Core Principles

The frontend should prioritize:

1. Desktop-first UX
2. Simple implementation
3. Clear feature-based organization
4. Reusable UI primitives
5. Consistent visual language
6. Minimal global state
7. Clear loading, empty, success, and error states
8. Accessibility where practical
9. Light and dark mode support
10. Avoiding unnecessary frontend abstractions

Do not introduce a new UI framework or state-management library without a concrete reason.

---

# 3. Styling

## Tailwind CSS

Use **Tailwind CSS** as the primary styling solution.

Tailwind should handle:

- Layout
- Spacing
- Responsive behavior
- Typography
- Colors
- Borders
- Shadows
- Light/dark themes
- Hover/focus states

Avoid introducing:

- CSS-in-JS
- Styled Components
- Emotion
- Multiple competing styling systems

Small amounts of regular CSS are acceptable for application-level behavior that is awkward to express with utility classes.

---

# 4. Component Library

Use **shadcn/ui** as the primary UI component system.

Common components include:

- Button
- Card
- Input
- Textarea
- Select
- Checkbox
- Switch
- Dialog
- Alert Dialog
- Dropdown Menu
- Popover
- Tooltip
- Tabs
- Table
- Badge
- Calendar
- Date Picker
- Sheet
- Sidebar
- Skeleton
- Toast/Sonner

shadcn components should live under:

```text
src/components/ui/
```

Example:

```text
src/components/
├── ui/
│   ├── button.tsx
│   ├── card.tsx
│   ├── dialog.tsx
│   ├── input.tsx
│   ├── select.tsx
│   └── table.tsx
│
└── layout/
    ├── AppLayout.tsx
    ├── AppSidebar.tsx
    └── AppHeader.tsx
```

Do not modify shadcn primitives for feature-specific behavior.

Create feature components that compose these primitives instead.

---

# 5. Icons

Use **Lucide React** as the default icon library.

Example navigation:

```text
LayoutDashboard   Dashboard
Wallet            Finance
ReceiptText       Transactions
ChartPie          Budgets
HeartPulse        Health
Dumbbell          Workouts
Target            Goals
Settings          Settings
```

Avoid mixing multiple icon libraries unless necessary.

---

# 6. Application Layout

Use a desktop dashboard layout.

Primary structure:

```text
┌─────────────────────────────────────────────────────────┐
│ App Header                                              │
├──────────────┬──────────────────────────────────────────┤
│              │                                          │
│ Dashboard    │ Page                                     │
│              │                                          │
│ Finance      │                                          │
│  Accounts    │                                          │
│  Transactions│                                          │
│  Budgets     │                                          │
│              │                                          │
│ Health       │                                          │
│  Weight      │                                          │
│  Workouts    │                                          │
│              │                                          │
│ Goals        │                                          │
│              │                                          │
│ Settings     │                                          │
│              │                                          │
└──────────────┴──────────────────────────────────────────┘
```

The sidebar should be the primary navigation mechanism.

Do not use bottom mobile navigation for the desktop application.

The sidebar may support collapsed and expanded states.

---

# 7. Feature Organization

Frontend code should primarily follow feature-based organization.

```text
src/
├── components/
│   ├── ui/
│   └── layout/
│
├── features/
│   ├── dashboard/
│   ├── finance/
│   ├── health/
│   └── goals/
│
├── hooks/
├── lib/
├── routes/
├── stores/
├── types/
└── main.tsx
```

Example Finance feature:

```text
features/finance/
├── api/
│   └── finance.api.ts
├── components/
│   ├── TransactionForm.tsx
│   ├── TransactionTable.tsx
│   ├── AccountCard.tsx
│   └── BudgetProgress.tsx
├── hooks/
│   └── useTransactions.ts
├── pages/
│   ├── FinancePage.tsx
│   ├── TransactionsPage.tsx
│   └── BudgetsPage.tsx
└── types.ts
```

Feature-specific components should remain inside their feature.

Move a component into `components/` only when it is genuinely shared across multiple features.

---

# 8. Server State

Use **TanStack Query** for data received from FastAPI.

Examples:

- Accounts
- Transactions
- Categories
- Budgets
- Weight logs
- Workouts
- Goals
- Dashboard summaries

Typical flow:

```text
React Component
      ↓
Feature Hook
      ↓
TanStack Query
      ↓
Feature API Client
      ↓
FastAPI
```

Example:

```text
TransactionTable
      ↓
useTransactions()
      ↓
finance.api.ts
      ↓
GET /api/v1/transactions
```

TanStack Query should handle:

- Fetching
- Caching
- Refetching
- Loading states
- Mutation states
- Query invalidation
- Server-state synchronization

Do not duplicate API data into Zustand.

---

# 9. Client State

Use local React state by default.

Use Zustand only when state genuinely needs to be shared across unrelated parts of the frontend.

Suitable examples:

- Sidebar state
- Shared UI preferences
- Complex cross-page temporary state

Do NOT use Zustand as a second cache for:

- Transactions
- Accounts
- Budgets
- Weight logs
- Workouts
- Dashboard data

Those belong to TanStack Query.

Preference order:

```text
Local component state
        ↓
URL / route state when appropriate
        ↓
TanStack Query for server state
        ↓
Zustand only for genuine global client state
```

---

# 10. Forms

Use:

```text
shadcn/ui
     +
React Hook Form
     +
Zod
```

for non-trivial forms.

Examples:

- Add transaction
- Edit transaction
- Create account
- Set monthly budget
- Add weight log
- Add workout
- Create goal

Example transaction form:

```text
Add Transaction

Type
[ Expense ▼ ]

Amount
[ 350.00 ]

Account
[ KBank ▼ ]

Category
[ Food ▼ ]

Date
[ 10/09/2026 ]

Note
[ Lunch ]

                 [Cancel] [Save]
```

Client-side validation improves UX but does not replace backend validation.

FastAPI/Pydantic remains the authoritative validation boundary.

---

# 11. Tables

Start with **shadcn Table**.

Example:

```text
Transactions

Search...                         September 2026 ▼

--------------------------------------------------------
Date        Category       Account                Amount
--------------------------------------------------------
10 Sep      Food           KBank                 -฿350
09 Sep      Transport      KBank                 -฿120
08 Sep      Salary         KBank              +฿32,750
--------------------------------------------------------
```

Do not introduce TanStack Table for simple tables.

Add TanStack Table only when advanced requirements appear, such as:

- Complex sorting
- Column visibility
- Advanced filtering
- Large datasets
- Complex pagination
- Row selection
- Reusable table infrastructure

---

# 12. Charts

Use **Recharts** as the default charting library.

Use charts for information where visualization provides meaningful value.

Finance examples:

- Monthly spending trend
- Income vs expense
- Spending by category
- Savings trend
- Budget progress

Health examples:

- Weight trend
- Workout frequency
- Workout duration
- Progress toward target weight

Dashboard examples:

```text
┌────────────┐ ┌────────────┐ ┌────────────┐
│ Balance    │ │ Expense    │ │ Savings    │
│ ฿45,200    │ │ ฿12,450    │ │ 21%        │
└────────────┘ └────────────┘ └────────────┘

Spending Trend
┌───────────────────────────────────────────┐
│                   ╭────╮                  │
│          ╭────────╯    ╰────╮             │
│     ╭────╯                   ╰──          │
└───────────────────────────────────────────┘
```

Prefer shadcn chart patterns built on top of Recharts where appropriate.

Do not add another charting library unless Recharts cannot reasonably satisfy a concrete requirement.

---

# 13. API Client

The frontend must communicate with FastAPI.

The desktop frontend must NEVER connect directly to Neon PostgreSQL.

Correct:

```text
React
  ↓
FastAPI
  ↓
SQLAlchemy
  ↓
Neon PostgreSQL
```

Incorrect:

```text
React
  ↓
Neon PostgreSQL
```

Database credentials must never be included in the desktop frontend bundle.

Centralize base HTTP configuration under something similar to:

```text
src/lib/api-client.ts
```

Feature-specific requests belong to the feature.

Example:

```text
features/finance/api/finance.api.ts
features/health/api/health.api.ts
```

---

# 14. Loading States

Every asynchronous screen must consider:

- Initial loading
- Refetching
- Empty state
- Error state
- Success state

Prefer skeleton components for initial page loading.

Example:

```text
Transactions

┌─────────────────────────────────────┐
│ ██████████    ███████    ████████  │
│ ███████       ███████    ████████  │
│ █████████     ███████    ████████  │
└─────────────────────────────────────┘
```

Avoid displaying a full-page spinner for ordinary data fetching where a skeleton provides better context.

---

# 15. Empty States

Empty states should explain what is missing and provide the next useful action.

Example:

```text
No transactions yet

Add your first income or expense to start tracking
your monthly finances.

[ + Add Transaction ]
```

Do not display only:

```text
No data.
```

---

# 16. Error Handling

API errors should be converted into understandable UI feedback.

Examples:

- Toast for failed mutations
- Inline validation errors for forms
- Error state for failed page queries
- Retry action where appropriate

Do not expose raw Python stack traces, SQL errors, or internal server errors to the user.

---

# 17. Theme

Support:

- Light
- Dark
- System

Default to System.

Theme should be handled globally.

Components must remain readable in both light and dark modes.

Avoid hard-coded colors when semantic theme tokens are available.

---

# 18. Responsive Design

The application is desktop-first.

Primary target:

```text
Desktop / Laptop
```

The UI should still behave reasonably at smaller window sizes.

However, do not compromise desktop UX merely to make the same interface suitable for phones.

A future mobile application may use a different UI built around the same FastAPI API.

---

# 19. Tauri Responsibilities

Tauri should primarily provide the native desktop shell.

Use Tauri APIs only when native desktop functionality is required.

Examples:

- Window management
- Native dialogs
- File system access
- Notifications
- System tray
- OS integrations

Normal business logic should remain in React or FastAPI.

Do not move ordinary finance or health business logic into Rust simply because the application uses Tauri.

---

# 20. Desktop Interaction Guidelines

Desktop interactions may use:

- Hover states
- Tooltips
- Keyboard shortcuts
- Context menus where useful
- Persistent sidebar
- Dense tables
- Multi-column layouts

Important actions should still be accessible without requiring hover.

Destructive actions should require confirmation where accidental execution could cause data loss.

---

# 21. Accessibility

Use semantic HTML where possible.

shadcn/Radix primitives should be preferred over custom implementations for complex interactive components.

Forms should have proper labels.

Interactive elements should have visible keyboard focus.

Icon-only buttons should have accessible labels or tooltips where appropriate.

---

# 22. Naming Conventions

React components:

```text
PascalCase.tsx

TransactionForm.tsx
TransactionTable.tsx
FinancePage.tsx
```

Hooks:

```text
useTransactions.ts
useAccounts.ts
useWeightLogs.ts
```

API modules:

```text
finance.api.ts
health.api.ts
goals.api.ts
```

Stores:

```text
ui.store.ts
preferences.store.ts
```

Avoid generic names such as:

```text
utils2.ts
helper.ts
common2.ts
stuff.ts
```

Names should describe responsibility.

---

# 23. Dependency Rules

Prefer:

```text
Page
 ↓
Feature Component
 ↓
Feature Hook
 ↓
Feature API
 ↓
Shared API Client
 ↓
FastAPI
```

Shared UI primitives must not depend on Finance or Health features.

For example:

```text
components/ui/Button
```

must NOT import:

```text
features/finance/*
```

Features may import shared components.

```text
features/finance
      ↓
components/ui
```

but shared UI should not import feature code.

---

# 24. Avoid Over-Engineering

Do not introduce abstractions before they solve a real problem.

Avoid creating:

- Generic CRUD frameworks
- Custom design systems on top of shadcn
- Large global stores
- Multiple API abstraction layers
- Repository patterns in the frontend
- Generic form engines
- Generic dashboard engines
- Complex event buses
- Micro-frontends

For V1, explicit code is preferred over premature generic abstractions.

If three similar implementations appear and a stable pattern becomes obvious, then consider extracting shared functionality.

---

# 25. MVP UI Scope

The first usable desktop version should focus on:

## Dashboard

- Current financial summary
- Monthly income
- Monthly expenses
- Savings
- Current weight
- Recent workout summary

## Finance

- Accounts
- Transactions
- Categories
- Monthly budgets

## Health

- Weight logs
- Workouts

## Goals

- Financial goals
- Weight goal

## Settings

- Theme
- Currency
- Basic application preferences

## Post-install flow

Use one compact welcome/sign-in screen. Discover the configured mode from FastAPI: username/password when Better Auth is active, or the existing personal-token form during activation. The desktop saves neither credentials nor session tokens. Show connecting, invalid-credentials, expired-session, and API-unavailable states. On success, open Dashboard. Guide empty states toward creating an account, recording a transaction, or beginning with Health. Avoid a multi-step wizard, sample data, and tutorial carousel.

Do not add advanced UI for future features before those features actually enter the implementation plan.

---

# 26. Future Mobile Client

The future mobile application should reuse:

```text
FastAPI
   ↓
Business logic
   ↓
Neon PostgreSQL
```

It does not need to reuse the desktop React UI.

Expected future architecture:

```text
Tauri Desktop ──┐
                │
                ▼
             FastAPI
                │
                ▼
              Neon
                ▲
                │
Mobile App ─────┘
```

Desktop may remain optimized for:

- Analytics
- Tables
- Reports
- Planning
- Detailed management

Mobile may focus on:

- Quick expense entry
- Quick weight entry
- Workout logging
- Today's summary

Do not make the desktop interface mobile-first solely to prepare for the future mobile client.

---

# 27. Source of Truth

This document is the source of truth for frontend and UI implementation decisions.

Coding agents should consult this document before:

- Adding a UI library
- Adding a state-management library
- Creating shared components
- Designing new feature folders
- Implementing forms
- Implementing tables
- Implementing charts
- Adding frontend dependencies

If implementation requirements conflict with this document, update the documentation intentionally rather than silently introducing a conflicting pattern.

The overall rule is:

> Prefer simple, explicit, feature-focused frontend code over premature abstraction.
