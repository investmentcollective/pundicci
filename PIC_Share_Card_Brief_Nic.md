# Design brief — PIC share card, Nic settles up (26 Sep 2026)

Hand this to Claude to generate the image. Self-contained; no other context needed.

---

## What to make

A single portrait image for an iMessage group of four. Nic has been three captain weeks in arrears since April. He is now putting the entire outstanding balance — plus this week's stake — on one two-leg multi. The card announces it and drives the group to The Pundicci Post.

The tone is not celebratory and not mocking. It is the moment before something happens.

**Canvas:** 1080 × 1920 px (9:16). Safe margin 72px all sides — iMessage crops tall images in thread previews, so nothing important within 72px of any edge.

**Format:** PNG. Must read as a thumbnail at ~300px wide: the headline and `$120.00` have to survive that.

---

## Brand

From the Pundicci Investment Collective design system. Do not substitute.

| Role | Hex |
|---|---|
| Ink / background | `#14181F` |
| Surface (cards on dark) | `#1E242E` |
| Hairline | `rgba(255,255,255,0.14)` |
| Primary text on dark | `#FFFFFF` |
| Muted text on dark | `rgba(255,255,255,0.55)` |
| **Nic (accent for this card)** | `#5B4FC7` |
| Win / positive | `#35D08A` |
| Loss / negative | `#FF7B80` |
| Alert / live | `#E8B44A` |

Dark/reversed treatment — ink background, white logo. **Nic's violet is the accent throughout this card**, replacing the amber used on the previous one. This is his moment.

**Type:** Jost (Google Fonts) — weights 400, 500, 800. Headline in Newsreader 800, the Post's masthead face.

**Logo:** Pundicci "P" monogram, white, top-centre, ~120px tall. Vector path:

```
M0 0 L560 0 L600 40 L600 230 L510 320 L250 320 L224 450 L61 450 L115 180 L395 180 L395 166 L126 126 Z
```
viewBox `0 0 600 450`, `fill="#FFFFFF"`.

Beneath it, Jost 500, ~11px, letterspaced 3.5px, uppercase, 55% white: `PUNDICCI INVESTMENT COLLECTIVE`

---

## Content — use verbatim

**Eyebrow** (Jost 600, letterspaced, `#5B4FC7`):
`THE LEDGER · SATURDAY 26 SEPTEMBER`

**Headline** (Newsreader 800, white, ~64px, tight leading):
`Nic has brought everything he owes.`

**Standfirst** (Jost 400, 55% white, ~26px):
`Four weeks of stakes. Two legs. One afternoon.`

### The stake block

A prominent panel, `#1E242E`, 20px radius, 4px `#5B4FC7` bar down the left.

- Label, Jost 500, 55% white, letterspaced: `SETTLING IN FULL`
- Figure, Jost 800, white, very large (~96px): `$120.00`
- Beneath, four small pills in a row (`rgba(91,79,199,0.16)` fill, `#5B4FC7` text, Jost 600, ~16px):
  `11 APR` · `9 MAY` · `1 AUG` · `26 SEP`
- Caption below the pills, Jost 400, 45% white: `Three outstanding captain weeks, plus today's.`

### Two leg cards

Each `#1E242E`, 16px radius, 1px hairline. Odds right-aligned in Jost 800, white.

**Each leg card carries an image strip across its top** — full card width, 200px tall, cropped to fill, with the card's top corners rounded to match. Two supplied images, attached with this brief:

- **Leg 1 → the MCG crowd photograph.** Wide shot of a packed Grand Final crowd from the stands. Crop centre-weighted; the arc of the stands and the green of the ground should both read.
- **Leg 2 → the Springbok character render.** A stylised springbok in a green South Africa jersey, gold chains, stadium behind. **This one is portrait-oriented — crop tight across the head and shoulders**, keeping the horns and the green jersey in frame. Do not letterbox the full figure into a wide band; it will read as a thin sliver of goat.

The two images are different registers — one is a documentary photograph, the other a stylised render. The treatment below is what pulls them together, so apply it to both:

- Lay a **flat** `rgba(20,24,31,0.50)` overlay across the whole strip. No gradients — the brand is flat, and a gradient scrim reads as a different design system.
- Desaturate the MCG crowd shot to roughly 35%. **Desaturate the Springbok render less — around 65%** — because the green jersey is what identifies the team, and washing it out loses the point of using it.
- The fixture line sits *over* the image, bottom-left, white, with the odds bottom-right. The selection line sits below the image on the solid card.
- If either image carries a visible watermark or source URL, crop it out rather than blurring it.

**Leg 1**
- Over photo — fixture, white 85%: `Fremantle v Brisbane Lions`
- Over photo — odds, Jost 800, white: `2.30`
- Below photo — selection, white, Jost 500, ~24px: `Brisbane Lions to win by 1–39`

**Leg 2**
- Over photo — fixture, white 85%: `Australia v South Africa`
- Over photo — odds, Jost 800, white: `1.35`
- Below photo — selection, white, Jost 500, ~24px: `South Africa`

Between or beneath the two cards, centred, muted: `COMBINED  3.105`

### The swing panel

The point of the card. Full width, two columns, divided by a hairline.

- Left column label, 55% white: `IF IT LANDS`
  Figure, Jost 800, `#35D08A`, ~56px: `+$255.54`
- Right column label, 55% white: `IF IT DOESN'T`
  Figure, Jost 800, `#FF7B80`, ~56px: `−$117.06`

Beneath, spanning both, Jost 400, 45% white, centred:
`The collective's season currently stands at +$2.94.`

Use a proper minus sign (−, U+2212) not a hyphen.

### Footer

- Jost 500, white: `Read it in The Pundicci Post`
- Beneath, Jost 400, 45% white, ~20px, in a subtle pill (`rgba(255,255,255,0.06)`):
  `investmentcollective.github.io/pundicci/#post`

---

## Layout order

1. Logo + wordmark
2. Eyebrow
3. Headline + standfirst
4. Stake block ($120 + the four week pills)
5. Two leg cards + combined odds
6. Swing panel
7. Footer

Newspaper front page, not betting app. Generous whitespace, strong hierarchy, flat fills and hairlines. No gradients, glows, shadows or emoji.

---

## Do not

- Use any bookmaker's name, logo or colours. This is the collective's card.
- Use "bet now", odds-comparison framing, or anything promotional.
- Round the figures. `$255.54`, `−$117.06`, `3.105` and `$2.94` are exact and the precision carries the tone.
- Make it look triumphant. Nothing has happened yet.
- Let the photographs set the tone. They are texture behind the numbers, not the subject. If a photo is competing with the figures for attention, darken it further.
- Stretch or squash either image to fit. Crop to fill and keep the aspect ratio.

---

## Source figures (for checking)

| | |
|---|---|
| Stake | $120.00 (4 × $30) |
| Leg 1 | Brisbane 1–39 margin @ 2.30 |
| Leg 2 | South Africa @ 1.35 |
| Combined odds | 3.105 |
| Return if it lands | $372.60 |
| Season net now | +$2.94 |
| Season net if it lands | +$255.54 |
| Season net if it loses | −$117.06 |

Season net = total returns minus total stakes across all 38 settled bets. Adding a $120 stake returning $372.60 moves it by +$252.60; a $120 stake returning nothing moves it by −$120.
