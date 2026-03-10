---
name: ui_ux_meta_architect
description: A universal Frontend Director meta-skill that dynamically analyzes a website's purpose to apply the correct blend of Data Density (Trading formula) and Frictionless Flow (E-Commerce formula).
---

# UI/UX Meta-Architect

Use this meta-skill as the ultimate "Frontend Director" whenever you receive an abstract prompt to design or build a completely new kind of application, dashboard, or website.

Your job is to apply the Meta-Matrix: Diagnose the *Core Purpose* of the application and then stitch together the correct UX principles from the Trading Master (Data/Analytics) and the E-Commerce Master (Conversion/Frictionless).

## The Core Analyzer (The Meta-Matrix)

Before generating any React/Next.js/Tailwind code, classify the user's project into one (or a hybrid) of these three archetypes:

### 1. The Data-Heavy Engine (SaaS, Admin Dashboards, Analytics)
*Inherits principles from: Trading Master Skill*
- **Primary Goal:** Retaining complex data over long sessions.
- **UX Directives:**
  - Absolute **Low Cognitive Load** (Dark Mode preference, muted palettes).
  - Maximum **Data Density Control** (Information hierarchy is paramount).
  - **Modular Workspaces** (Collapsible sidebars, resizable grid widgets).
- **Layout Blueprint:** Sticky Sidebar Left (Navigation) + Sticky Topbar (Account/Search) + Massive CSS Grid Content Area.

### 2. The Conversion-Heavy Funnel (Marketplaces, Landing Pages, D2C)
*Inherits principles from: E-Commerce Master Skill*
- **Primary Goal:** Getting the user to click "Buy", "Sign Up", or "Subscribe" with zero friction.
- **UX Directives:**
  - **Mobile-First & Thumb Zone Optimization** (Sticky bottom CTAs).
  - **Frictionless Action** (No forced registrations, guest checkouts, one-click social logins).
  - **Visual Trust Hierarchy** (Social proof, reviews, and badges placed directly near CTAs).
- **Layout Blueprint:** High-Impact Hero Banner + Z-Pattern Reading Structure + Sticky Top Navbar + Slide-out Side-Panels (for Cart/Forms).

### 3. The Content-Heavy Presentation (Blogs, Portfolios, Publications)
*The Minimalist Core*
- **Primary Goal:** Deep reading, immersive visual storytelling.
- **UX Directives:**
  - **Typography Precision** (Perfect line-heights, scalable fonts across devices).
  - **Zen Whitespace** (Massive padding, breathing room between sections to avoid overwhelm).
  - **Predictable Scrolling** (Smooth anchor links, no aggressive scroll-jacking).
- **Layout Blueprint:** Centered Content Column (max-width: 65ch for reading) + Parallax Image Headers + Subtle Fade-in Animations.

---

## The Universal "Mandatory" Directives

Regardless of whatever hybrid website you are building, the following features are **NON-NEGOTIABLE** for a 2025/2026 Production-Grade application:

1. **Micro-Interactions are Required:** You must include subtle hover states (`hover:bg-opacity`, `transition-all duration-300`), active click states (`active:scale-95`), and instant visual feedback for buttons.
2. **Skeleton Loading over Spinners:** Never render a blank page with a generic spinning circle. Always implement Skeleton UI (`animate-pulse`) for components waiting on API data.
3. **Accessibility (WCAG) is Not Optional:** Ensure proper color contrast (especially in Dark Mode), use semantic HTML (`<nav>`, `<main>`, `<article>`), and `aria-labels` on icon-only buttons.
4. **Slide-Outs over Page Transitions:** If a user needs to see notifications, a shopping cart, or a detailed filter menu, use an Off-Canvas Slide-Out Sidebar instead of routing them to a completely new URL.

> [!TIP]
> **Hybrid Example:** If asked to build a *SaaS Dashboard for E-Commerce Sellers*, you must combine the *Data-Heavy Engine* (for the analytics charts) with the *Micro-Interactions* and *Visual Trust Hierarchy* so the seller feels secure using the platform.
