# Brand guide: Buy it again prototype

Updated: 22 October 2026. Written with Claude. The visual page version is `01_Project/Assets/brand_guide.html`.

This guide records how the Buy it again prototype looks, sounds and behaves, so the portfolio, screenshots and any future app stay consistent. It's for this independent project. It isn't Instacart's brand guide and doesn't replace it.

## 1. What this project is

**Name:** Buy it again (Instacart-inspired concept).
**One line:** Up to five familiar groceries, ranked from a shopper's own order history, so returning shoppers can rebuild a basket with less searching.
**Status:** an independent portfolio project built on Instacart's public 2017 order data. It isn't made for, connected to or endorsed by Instacart. AI help came from Codex and Claude.

Justin wants the shopping page to look like a focused product, without demo wording, portfolio tabs or explanatory disclaimer blocks. Keep the independent-project relationship clear in the project guide and case study instead: “Independent portfolio concept inspired by Instacart's brand. Not affiliated with or endorsed by Instacart.” Photo sources and credit stay in project documentation; there is no credit footer in the shopping page.

## 2. Relationship to the Instacart brand

The look follows Instacart's public website and brand guide (heyitsinstacart.com, checked 22 October 2026), so the concept feels like it could live in their app. That means using their colour names and rules, but not claiming their identity.

| Do | Don't |
|---|---|
| Use the colour palette and usage rules below | Say or imply the project is Instacart's work |
| Use an official Instacart logo file only if you've obtained it legitimately, unmodified, with the disclaimer nearby | Redraw, recolour, stretch or recreate the logo or carrot |
| Use stock photos with a clear licence | Copy Instacart's product photos or marketing images |
| Name the data source: "Instacart's public 2017 order dataset" | Present offline scores as Instacart results or business impact |

**Header logo and tab icon:** the header now embeds the official full-colour dark Instacart logo served on instacart.ca, unmodified, saved as `03_Code/05_Prototype/assets/instacart_logo.svg`. This replaces the separate carrot plus typed text. The browser-tab icon uses the unmodified public brand-site carrot, also saved as `03_Code/05_Prototype/assets/instacart_carrot.png`. Both are embedded for offline use. Source URLs and hashes are recorded in `01_Project/Assets/prototype_image_sources.json`. Independent-project context remains in the portfolio and project documentation, outside the shopping UI.

## 3. Colour

Names come from Instacart's brand guide. Values were read from the public site and guide pages, not from an official token file.

### Brand colours

| Token | Name | Hex | Role in the prototype |
|---|---|---|---|
| `--kale` | Kale | `#003D29` | Dark brand colour: headings on light backgrounds, tag text, selected states |
| `--cashew` | Cashew | `#FAF1E5` | Warm surface for notes and highlights |
| `--honeydew` | Honeydew | `#C5FF96` | Light highlight: "Default" badges, Undo text on dark toast |
| `--cantaloupe` | Cantaloupe | `#FFBB6E` | Restrained warm accent; use rarely |
| — | Carrot | `#FF7009` | Logo mark only. Not for backgrounds, body text or buttons |
| — | Lime | `#0AAD0A` | Logo leaf only. Not for backgrounds or body text |

### Interface colours

| Token | Hex | Role |
|---|---|---|
| `--cta` | `#108910` | Primary buttons (Add). The accessible green used on instacart.ca |
| `--cta-hover` | `#0B700B` | Button hover and pressed |
| `--cta-soft` | `#E7F5E7` | Basket count badge, soft success |
| `--ink` | `#242529` | Main text, selected tab |
| `--ink-2` | `#5E6066` | Secondary text, row subtitles |
| `--ink-3` | `#6E7075` | Small labels (aisle names, notes, footer) |
| `--line` | `#E8E9EB` | Dividers and card borders |
| `--chip` | `#F0F1F3` | Search bar, chips, notices |
| `--img-bg` | `#F6F7F8` | Photo placeholder background |
| — | `#1D1E21` | Reviewer bar only, to keep it visibly separate from the store |

### Colour rules (from Instacart's guide, applied here)

- Carrot and Lime are spot colours. Never backgrounds or body text.
- Neutrals aren't used for call-to-action buttons. Primary actions are green.
- Don't use dark neutrals as page backgrounds (the reviewer bar is a deliberate exception: it's a demo tool, not the store).
- Don't create new tints, shades or off-brand colours.
- Every text pairing must meet WCAG AA contrast (a readability standard: at least 4.5:1 for normal text, 3:1 for large text).

### Checked contrast (calculated 22 October)

| Pairing | Ratio | Passes AA for small text? |
|---|---|---|
| White on `--cta` green | 4.56:1 | Yes, just. Keep button text at 14px bold or larger |
| Kale on white | 12.36:1 | Yes |
| Kale on Honeydew | 10.66:1 | Yes |
| Kale on Cashew | 11.05:1 | Yes |
| Ink on white | 15.31:1 | Yes |
| Ink-2 on white | 6.29:1 | Yes |
| Ink-3 `#6E7075` on white | 4.96:1 | Yes (changed from `#8A8C91`, which was 3.36:1) |
| Honeydew on Ink (Undo in toast) | 13.21:1 | Yes |
| Carrot on white | 2.77:1 | No. Another reason it's logo-only |

These are calculated ratios, not an accessibility audit.

## 4. Typography

- **Typeface:** Inter (free, Google Fonts), standing in for Instacart Sans, which is Instacart's own font and isn't available to us. Fallback: Arial, sans-serif.
- **Weights:** 400 regular, 500 medium (product names), 600 semibold (buttons, tabs, tags), 700 bold (headings, Add), 800 (text logo fallback only).

| Use | Size / weight |
|---|---|
| Page title (Compare, About) | 28px / 700, Kale |
| Section title ("Buy it again", "Browse") | 22px / 700 |
| Basket title | 18px / 700 |
| Body | 15px / 400, line height 1.4 |
| Product name | 15px / 500, two lines max |
| Buttons and tabs | 14px / 600–700 |
| Aisle label, notes | 13px / 400, Ink-3 |
| Tags | 12px / 600 |
| Footer, fine print | 12px |

Sentence case everywhere ("Buy it again", not "Buy It Again"). Numbers in tables use tabular figures so columns line up.

## 5. Spacing and shape

- **Spacing:** based on a 4px step, mostly 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48. Cards in a row are 20px apart; sections are 48px apart.
- **Page:** max width 1280px, 24px side margins (16px on phones).
- **Corners:** pills fully rounded (buttons, chips, search, tabs); photos 14px; basket panel 18px; notices 14px; tags 6px.
- **Elevation:** almost flat. Light shadow only on floating things (Add button on a photo, menus, toast, phone basket sheet).

## 6. Components

| Component | Rules |
|---|---|
| Product card | Square photo with rounded corners and a faint edge, Add button bottom-right on the photo, name (max two lines), aisle label underneath. Photo zooms slightly on hover |
| Add button | Green pill "+ Add". After adding: white pill with green outline, "✓ Added". Tap again to remove. No quantities (the data has none) |
| Tag | White label top-left of the photo, Kale text. Only "Often bought" or "Last order", at most two per row, and only when true for that shopper |
| ••• menu | Top-right of Buy it again cards only. One action: “Hide” |
| Toast | Dark pill at the bottom: "[Product] hidden from Buy it again", with Undo in Honeydew. Disappears after about 6 seconds |
| Hidden items | Link beside the row title, "Hidden items (n)". Opens a list with "Show again" |
| Basket panel | Right side on desktop, with a count badge, thumbnail, name and Remove. On phones: green bottom bar that opens a sheet |
| Notices | Grey rounded box with a bold first line, a short second line and one button if needed (Try again, etc.) |
| Loading | Grey placeholder cards that gently pulse (no pulse if the device asks for reduced motion) |
| Shopper selector | Rounded A/B/C button beside search with a rounded popup aligned beneath it; no reviewer bar or state-testing controls |
| Navigation | No portfolio tabs in the shopping page; comparisons and About material live in project documentation |

## 7. Voice and copy

Shopper-facing copy sounds like a calm grocery app: short, plain, no hype.

| Write | Avoid |
|---|---|
| "Buy it again" | "Your AI-powered picks!" |
| "Often bought", "Last order" | "Bought in 9 of 12 earlier orders" (fine in analysis, not in the store) |
| "Popular with all shoppers, not based on your orders" | Unlabelled popular items mixed in with personal ones |
| "Couldn't load your past items" | "Error 500" or blaming the shopper |
| "Hide from Buy it again" | "Not interested", "Dislike" (Hide isn't a preference signal) |
| "Show again" | "Restore preference" |

Method explanations live in project documentation, not the shopping page.

Portfolio and documentation copy follows the project rules: first person, casual, contractions, honest about AI help, and clear about what's measured versus assumed. Use "percentage points" for differences between percentages.

## 8. Imagery

- Free stock photos from Unsplash (Unsplash licence), showing the kind of product, not the exact branded item. Retain photo sources and Unsplash credit in project documentation and Assets/prototype_image_sources.json, rather than the shopping UI.
- Photos are embedded in the prototype file so it works offline and in file previews.
- No Instacart product photography, no packaging that shows other brands' logos where avoidable, no people's faces.
- If a photo fails, show the soft placeholder (bag icon on a light aisle colour), never a broken-image icon.
- Swap a photo if it doesn't read as the product at card size (Half & Half is currently a weak match).

## 9. Data and honesty rules for visuals

- Product names are exact catalogue names. Banana and Bag of Organic Bananas are different products.
- No invented prices, sizes, stock, delivery times or checkout.
- A/B now use exported real historical summaries and saved rankings; C is a labelled simulated new shopper. Don't describe the latter as measured new-customer evidence.
- Results charts and tables use the verified final numbers and say they're offline results.

## 10. Using this in the portfolio

- Screenshot at 1366px wide (desktop) and 390px (phone). Show Buy it again with one "✓ Added" and the basket filled, plus one Hide → Undo moment.
- Put the independent-project disclaimer alongside portfolio screenshots and in the case study; it is no longer part of the shopping interface.
- Caption screenshots with what's real and what's sample.
- Credit AI help: "Built with AI assistance (Codex for analysis and code, Claude for the prototype design)."
- Reuse the colour tokens from section 3 for any charts so the case study matches the prototype.

## Open items

- Official full-colour header logo and carrot browser-tab icon added.
- Real A/B examples connected; C remains simulated.
- No usability test or accessibility audit yet.


## Product photos restored for real examples

All 19 familiar candidates across A/B now have embedded illustrative photos, including those revealed after Hide. Existing photos were retained; matching milk, yogurt, apple and pear imagery was reused, and new stock photos cover drinks, jerky, nuts, cheese, cereal, cups, popcorn, paper towels, almond butter and chocolate. These show a product type, not exact packaging, flavour, nutritional properties or shape. Sources and image hashes are saved in Assets/prototype_image_sources.json. The styles, recommendation payload and model results weren't changed. Local code/data checks passed; the browser tool blocks file URLs, so a visual check in Justin's existing Chrome tab remains pending.
