# Visualization

This file documents all data visualization components in Chess960 WZ.
All screenshots are located in `screenshots/visualization/`.

---

## Overview

The analytics dashboard is accessible from **Main Menu → History & Stats → Interactive Analytics**.
It contains 7 interactive chart types, each filterable by side (Both / White Only / Black Only).

Screenshot: `screenshots/visualization/dashboard_overview.png`

> _(Replace with actual screenshot — show the full dashboard with buttons visible)_

---

## Chart 1 — Piece Dependency (Pie Chart)

**Screenshot:** `screenshots/visualization/chart_piece_dependency.png`

This pie chart shows what percentage of all moves were made with each piece type (pawn, rook, knight, bishop, queen, king). A player who relies heavily on pawns and a single piece type may have a more predictable style. The chart helps identify over-dependence on specific pieces.

---

## Chart 2 — Think Time by Phase (Line Chart)

**Screenshot:** `screenshots/visualization/chart_think_time.png`

Plots average think time (seconds per move) across three game phases:
- Opening (moves 1–10)
- Middlegame (moves 11–30)
- Endgame (moves 31+)

Longer think time in the opening may indicate unfamiliarity with Chess960 positions. A spike in the endgame can reflect complex calculation in reduced-material situations.

---

## Chart 3 — Capture Hesitation (Bar Chart)

**Screenshot:** `screenshots/visualization/chart_capture_hesitation.png`

Shows the average thinking time before making a capture, grouped by piece type. Pieces with high average capture-time suggest the player deliberates more before using them aggressively.

---

## Chart 4 — Lethality Matrix (Stacked Bar Chart)

**Screenshot:** `screenshots/visualization/chart_lethality.png`

A cross-tabulation of attacker piece vs captured piece. The x-axis is the piece that made the capture; each colored segment shows what it captured. Reveals which pieces are most effective at taking opponents and which enemy pieces are most often lost.

---

## Chart 5 — Win Rates (Pie Chart)

**Screenshot:** `screenshots/visualization/chart_win_rate.png`

Displays the overall win percentage for White, Black, and draws across all recorded games. Useful for detecting whether the board flip or time control choice creates a systematic advantage for one side.

---

## Chart 6 — Duration Distribution (Histogram)

**Screenshot:** `screenshots/visualization/chart_duration_dist.png`

A histogram of game durations in minutes. Shows whether most games end quickly (time pressure or early checkmates) or run close to the full time control.

---

## Chart 7 — Move Count Trend (Line Chart)

**Screenshot:** `screenshots/visualization/chart_move_trend.png`

Plots the total number of half-moves across successive games (game sequence on x-axis). An upward trend may indicate longer, more strategic games over time as players improve.
