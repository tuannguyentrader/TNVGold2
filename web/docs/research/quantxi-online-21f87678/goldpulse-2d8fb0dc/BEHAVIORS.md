# GoldPulse Behaviors

- Initial page uses a dark analytics dashboard with a fixed bottom subscription bar.
- Disclaimer banner can be dismissed; the full-disclaimer link anchors to the footer.
- Hero `Manage` opens an API key modal; valid input shows a saved state before closing. The bell opens a notification modal.
- Upgrade CTA opens a TNV PRO modal. The modal can be closed and its checkout action is demo-only.
- Action banner share button copies a status string and temporarily changes to a check icon. Its bell opens the notification modal.
- Metric cards with multi-timeframe content flip on click. Info icons expose hover tooltips.
- Live gold price chart responds to pointer hover with a vertical guide, point marker, and price context.
- Gold Session Flow tabs switch between Session Flow and TradingView Live views. Checkbox controls toggle price, pulse, sessions, and EMA layers. Timeframe and range buttons update active styling. Hovering the SVG updates the inspector row.
- Footer policy links show demo alerts.
- Fixed subscribe bar opens the notification/subscription modal and can be dismissed.

Responsive observations: at 1440px the dashboard is multi-column; at 390px the content stacks, header center status is hidden, controls wrap, and the history table requires horizontal scrolling.
