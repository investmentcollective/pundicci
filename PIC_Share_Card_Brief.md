# Design brief — PIC share card, 12 Sep 2026

Hand this to Claude to generate the image. Everything needed is below; no other context required.

---

## What to make

A single portrait image for sharing to an iMessage group of four. It announces three live bets riding on tonight's football and this afternoon's races, and drives the group to The Pundicci Post.

**Canvas:** 1080 × 1920 px (9:16). Safe margin 72px all sides — iMessage crops the edges of tall images in the thread preview, so nothing important within 72px of any edge.

**Format:** PNG. Must be legible as a thumbnail in a message list, so the headline and the `$837.50` need to survive being shrunk to roughly 300px wide.

---

## Brand

Taken from the Pundicci Investment Collective design system. Do not substitute.

| Role | Hex |
|---|---|
| Ink / background | `#14181F` |
| Surface (cards on dark) | `#1E242E` |
| Hairline | `rgba(255,255,255,0.14)` |
| Primary text on dark | `#FFFFFF` |
| Muted text on dark | `rgba(255,255,255,0.55)` |
| Charlie | `#127A5E` |
| Shannon | `#B85C22` |
| Win / positive | `#35D08A` |
| Alert / live | `#E8B44A` |

**This card is the dark/reversed treatment** — ink background, white logo. The dashboard is white-dominant, but a share card competes in a message thread and needs to hold its own.

**Type:** Jost (Google Fonts) for everything except the headline. Weights 400, 500, 800. Headline in Newsreader 800 — it's the Post's masthead face and signals this is an article, not a bet slip.

**Logo:** the Pundicci "P" monogram, white, top-centre, ~120px tall. Vector path:

```
M0 0 L560 0 L600 40 L600 230 L510 320 L250 320 L224 450 L61 450 L115 180 L395 180 L395 166 L126 126 Z
```
viewBox `0 0 600 450`, `fill="#FFFFFF"`.

Under it, in Jost 500, 11px equivalent, letterspaced 3.5px, uppercase, at 55% white: `PUNDICCI INVESTMENT COLLECTIVE`

---

## Content — use this copy verbatim

**Eyebrow** (Jost 600, letterspaced, `#E8B44A`):
`LIVE · SATURDAY 12 SEPTEMBER`

**Headline** (Newsreader 800, white, ~64px, tight leading):
`Brisbane carry two men's money tonight.`

**Standfirst** (Jost 400, 55% white, ~26px):
`Neither asked the other first.`

### Three bet cards

Each on `#1E242E`, 20px radius, 1px hairline border, with a 4px accent bar down the left edge in the member's colour.

**Card 1 — accent `#127A5E`**
- Member chip: `CHARLIE`
- Title: `12-leg SGM · Brisbane v Adelaide`
- Meta line: `Gabba · 19:35 · $25 bonus @ 32.00`
- Figure, right-aligned, Jost 800, `#35D08A`: `$775.00`

**Card 2 — accent `#127A5E`**
- Member chip: `CHARLIE`
- Title: `Ahha Ahha · Rosehill R9 (Place)`
- Meta line: `16:40 · $10 @ 6.25 · the February horse, again`
- Figure: `$62.50`

**Card 3 — accent `#B85C22`**
- Member chip: `SHANNON`
- Title: `AFL Premiership Exacta`
- Meta line: `Brisbane 1st, Sydney 2nd · $10 @ 18.00 · leg one is tonight`
- Figure: `$180.00`

### Total strip

Full-width band beneath the cards, slightly lighter than the background:

- Left, Jost 500, 55% white: `COMBINED IF THEY ALL LAND`
- Right, Jost 800, `#35D08A`, largest number on the card (~72px): `$1,017.50`
- Below, small, 45% white: `Charlie's actual cash outlay this weekend: $10.00`

That last line is the joke. Give it room.

### Footer

- Jost 500, white: `Read it in The Pundicci Post`
- Beneath, Jost 400, 45% white, ~20px: `investmentcollective.github.io/pundicci/#post`

Set the URL in a subtle rounded pill (`rgba(255,255,255,0.06)` fill) so it reads as tappable even though the image isn't.

---

## Layout order, top to bottom

1. Logo + wordmark
2. Eyebrow
3. Headline + standfirst
4. Three bet cards, stacked, even gaps
5. Total strip
6. Footer

Vertical rhythm should feel like a newspaper front page, not a betting app: generous whitespace, strong hierarchy, no gradients, no glows, no drop shadows, no emoji. Flat fills and hairlines only.

---

## Do not

- Use any bookmaker's name, logo or colours. This is the collective's card, not Sportsbet's.
- Add odds-comparison framing, "bet now" language, or anything resembling a promotion.
- Use gradients, glows or 3D effects — the brand is flat and the logo is hard-edged.
- Round `$1,017.50` or drop the cents. The precision is part of the tone.

---

## Source figures (for checking)

| Bet | Stake | Odds | Return |
|---|---|---|---|
| Charlie — 12-leg SGM | $25 (bonus) | 32.00 | $775.00 |
| Charlie — Ahha Ahha place | $10 | 6.25 | $62.50 |
| Shannon — Premiership Exacta | $10 | 18.00 | $180.00 |
| **Combined** | **$10 cash** | — | **$1,017.50** |

Bonus-bet stakes are not returned, which is why the SGM pays $775 and not $800.
