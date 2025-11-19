# UX / UI Options for the CEO Discovery Dashboard

The current pixel-art office UI can evolve along three complementary axes so
that different stakeholders (CEO, COO, product squads) always see actionable
context.

## 1. Layout Modes
1. **Command Deck (default desktop)**
   - Left: Treasury + runway meters
   - Center: Active projects timeline with drag-to-expand cards
   - Right: Discovery feed (patterns, proposals, pain points)
2. **Ops Wallboard (large displays)**
   - Full-width grid with auto-rotating spotlight tiles showing: treasury trend,
     top ROI proposals, orchestrator queue health, and agent availability.
3. **Tablet Stack (field reviews)**
   - Vertical stack of collapsible accordions with sticky KPIs so leadership can
     approve proposals while walking the floor.

## 2. Interaction Patterns
- **Contextual approvals** – Each proposal card exposes "Approve", "Request
  Revisions", and "Archive" buttons that emit REST calls and immediately update
  the WebSocket feed for everyone online.
- **Pattern drill-downs** – Clicking a pattern opens a side sheet showing root
  cause notes, similar historical occurrences, and linked projects.
- **Runway simulators** – Adjust burn rate sliders to preview runway impact; the
  UI replays economy snapshots without mutating production data.

## 3. Visual Language
- **Status colors** – Use BeCoin orange for actionable, teal for healthy, and
  muted gray for idle/queued items.
- **Motion cues** – Subtle easing on proposal entry/exit animations keeps focus
  without distracting from financial readouts.
- **Accessibility** – Minimum 4.5:1 contrast, keyboard navigation for every
  button, and ARIA live regions on WebSocket-driven notifications.

## 4. Notifications & UX Copy
- Show "Next discovery scan in <N> minutes" timer sourced from the WebSocket
  heartbeat.
- Use warm, human copy ("All quiet on the proposal front") when lists are empty.
- Provide toast confirmations when executives trigger orchestrator actions so
  they trust the automation loop.

These options give design + engineering concrete hooks for iterative delivery
without rewriting the dashboard front end.
