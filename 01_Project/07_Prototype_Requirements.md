# Prototype requirements: Buy again

Updated: 22 October 2026. Written with Claude from the agreed brief, the Claude handoff and the research plan. These are design requirements for the prototype, not evidence that shoppers want the feature.

## What the prototype is for

Let a reviewer see how the selected weighted-recency method would feel as a shopping feature: pick an example shopper, see up to five familiar products with a plain reason, add some to a demo basket, hide one, restore it, and find how the method was chosen.

It's an independent portfolio concept in an Instacart-inspired style. It isn't made for, approved by or connected to Instacart. The independent-project relationship is documented in the guide and case study; Justin removed explanatory labels from the shopping page.

## Shopping screen

Justin simplified the product UI on 22 October. The page now shows Buy it again, search, broad browse categories and the basket. Removed Try it / Compare methods / About navigation and those portfolio sections from the prototype. Model comparisons and project explanations remain in the project guide and saved results.

The header retains a simple Shopper A/B/C selector to switch example histories. No reviewer bar, visible loading/error state selector, Reset demo, demo labels or explanatory disclaimer blocks. Basket is labelled “Basket.” Photo sources and credits live in project documentation, not the shopping footer. This remains a local portfolio prototype in the project documentation; it isn't a live Instacart service.

## Buy again rules

1. Show up to five distinct products from that shopper's own history, ranked by weighted recency.
2. Each card looks like a normal store card: photo, Add button on the photo, product name (exact catalogue name) and aisle.
3. No counts like "Bought in 9 of 12 earlier orders" (Justin's decision: real apps don't show that). Instead, at most two cards per row get a quiet tag: "Often bought" (bought in at least half of earlier orders) or "Last order" (in the most recent order). Tags must stay true to the shopper's history.
4. Add is optional. Nothing goes into the basket automatically.
5. Ignoring a card is no action. There's no Skip button.
6. Hide removes only that exact product ID. Hiding Banana doesn't hide Bag of Organic Bananas.
7. Hidden products are filtered out before picking the top five. The next eligible product fills the gap. If none is left, show fewer cards.
8. Hide sits in a ••• menu on the card, labelled “Hide.” After Hide, show an Undo message for a few seconds. "Hidden items (n)" next to the row title opens a list with Show again. Hiding doesn't remove the product from the basket.
9. Restore makes the product eligible again. It only reappears if it ranks in the top five.
10. Hidden items are saved per example shopper in the same browser. This is a demo of the planned behaviour, not an account or cross-device sync.

## States to design

| State | What the shopper sees |
|---|---|
| Normal | Five cards |
| Added | Add button changes to "✓ Added" (tap again to remove); product appears in the basket |
| Hidden | Card leaves, next one fills in, Undo message appears |
| Restored | Product is eligible again; may or may not reappear |
| Short list | Fewer than five cards; no filler products |
| Empty (all hidden) | "No items to show" with Manage hidden items |
| No history | Row becomes "Popular right now", labelled "Popular with all shoppers, not based on your orders" (real top five); no Hide menu |
| Loading | Grey placeholder cards |
| Error | "Couldn't load your past items" with Try again; search and browsing still work |

## Basket

- Demo basket lists added products with Remove. No quantities (the data has none).
- Following the project rules: no prices, sizes, checkout, payment, delivery or stock. Justin briefly chose sample prices and a demo checkout on 22 October, then reversed it the same day.

## Content rules

- Use real product names from `products.csv`. Banana and Bag of Organic Bananas are different products.
- No invented prices, sizes or stock.
- Photos are free stock photos from Unsplash (Justin's decision), with sources retained in Assets/prototype_image_sources.json and the brand guide. They show the kind of product, not the exact item.
- Header: official full-colour dark Instacart logo, unmodified from the public instacart.ca asset; saved as instacart_logo.svg and embedded in the page. Browser-tab icon is the official carrot PNG. Sources are recorded in Assets/prototype_image_sources.json.
- Shoppers A and B now use real historical summaries and frozen weighted-recency rankings: 10 earlier orders/18 familiar candidates and five earlier orders/one candidate. C is a simulated no-history example. The demo labels these separately. All candidates are exported for Hide replacements; final basket answers aren't included.
- Don't describe anyone's diet or reasons for buying.
- Results tables use the verified final numbers from `05_Results/03_Checks/final_evaluation.json` and say they're offline results, not app performance.

## Visual style

Taken from the public Instacart site and brand guide, checked 22 October 2026. Swatch names come from the brand guide; values were read from the pages, not from an official token file.

| Use | Colour |
|---|---|
| Page background / warm surfaces | Cashew `#FAF1E5` |
| Dark brand areas, headings on cream | Kale `#003D29` |
| Light highlight (selected tags) | Honeydew `#C5FF96` |
| Restrained warm accent | Cantaloupe `#FFBB6E` |
| Primary buttons (accessible green from the site) | `#108910` with white text |
| Body text | `#242529` |
| Neutral chips | `#E8E9EB` |
| Carrot `#FF7009` | Logo mark only; brand guide says don't use as background or body text |

- Font: Instacart Sans is Instacart's own typeface, so the prototype falls back to a similar free sans (Inter).
- Shapes: pill buttons (fully rounded), 12px photo corners, grey rounded search bar, dark pill for the selected tab.
- Brand guide rules followed: Carrot and Lime aren't used as backgrounds or body text; neutrals aren't used for call-to-action buttons; Kale is the dark brand surface.
- Spacing: 8px grid (8, 16, 24, 32).

## Accessibility intent

- Text pairs aim for WCAG AA contrast (a readability standard; 4.5:1 for normal text).
- Every button is reachable by keyboard and has a visible focus ring.
- Undo and basket updates are announced to screen readers.
- This is design intent. No accessibility audit has been done.

## Figma and the build

- Decision (22 October): web prototype now, Figma later only if design files are needed. `03_Code/05_Prototype/buy_again_prototype.html` runs in a browser and uses exported real A/B history summaries and saved weighted-recency rankings; C is simulated. It doesn't retrain or run Python in the browser.
- To get it into Figma: connect the Figma connector in Claude, or import the HTML with a Figma plugin such as html.to.design, then turn repeated parts into components.
- Components to make in Figma later: Product card (default / added / tagged / menu open), Add button, Basket row, Basket panel, Toast, Skeleton card, Tab, Reviewer bar.

## Still open

- Real examples are connected. Next check the page in Chrome and plan a small usability test. No-history C is simulated, not a real measured new-customer case.
- Streamlit or a custom web app for the working version.
- Prototype test plan (task, timing, who) hasn't been agreed or run.


## Real-data connection with the approved design

The current project HTML now uses real A/B summaries and all their ranked familiar candidates. A has 10 earlier orders and 18 candidates; B has five earlier orders and one candidate. C remains a labelled simulated no-history example. The exporter preserves the existing CSS, photos and seven broad browsing categories; it doesn't add a shopper banner. These categories are display groups, not original aisle labels. Products without photos use the existing placeholder. Initial lists match saved predictions and code-level interaction checks pass. Justin's review of this connected version is still pending. The Downloads reference is unchanged; open the project copy for real data.


### Image update — 22 October

All 19 familiar candidates in the real A/B examples now have embedded illustrative product-type photos. New photos don't change rankings or history; exact packaging isn't represented. The public official carrot icon is embedded too, so it works offline. Layout and CSS stay unchanged. Justin's visual review is pending; code-level image and interaction checks passed.


### Copy and navigation — current decision

Keep the shopping page focused on using the feature. Hide menu is “Hide,” the toast is “[Product] hidden,” and restore stays “Show again.” No tutorial paragraph in Hidden items. C shows “Popular products” without a personalised label. Loading/error renderers remain in code for state handling, but there is no visible state-testing dropdown. Add/remove, Hide/Undo, list replacement, A/B/C switching, search, Home and basket controls passed JavaScript checks after removing the tabs. Images and recommendation data stayed unchanged. Human review of this simplified page is next.


### Header selector and empty basket

The shopper switch sits immediately after search, with no auto-pushed right margin. Both trigger and popup are rounded; the popup aligns to the left edge of the trigger and supports arrows, Enter/Space, Escape and outside-click dismissal. A/B/C selection and per-shopper hidden storage are unchanged. Empty basket: “Your basket is empty. Add an item to get started.” No photo-credit footer appears in the shopping page; attribution/provenance stays in project files. Code-level interaction checks passed; visual review remains with Justin.

## Discovery prototype added — 23 October 2026

Justin authorised the UI extension after the reserved check. The local shopping page now has a separate “You might also like” row between Buy it again and Browse, using up to three unfamiliar items from the unchanged discovery method. Existing A/B histories personalise the saved development-fitted relationships; no target baskets are read or models refitted for the export. These are illustrative V1 example shoppers, not the audit sample.

A: Trail Mix, Clementines, Crunchy Oats 'n Honey Granola Bars. B: Trail Mix, Soda, Clementines. C retains its popular section with no duplicate discovery row. Add/toggle/remove use the existing basket. Familiar-item Hide remains unchanged; discovery doesn't have Hide in this first UI iteration. New products use neutral placeholders unless an embedded photo already exists. Source names are retained; display categories are simplified.

The original V1 study URLs suppress discovery and retain their original browse/search catalogue. CSS, old photos, Buy again data and hidden-item storage keys are unchanged. The pre-discovery HTML is archived at 99_Archive/02_Prototype_Revisions/buy_again_before_discovery.html. Claude's portfolio site/copy wasn't edited.

Checks passed in a Node VM with a stub DOM: A/B exclusions, Add/toggle/remove event handlers, search, familiar Hide separation, C, loading/error suppression and original study conditions. This isn't browser visual review, accessibility certification or user testing. Export/check reports: 05_Results/03_Checks/discovery_demo_export.json and discovery_prototype_checks.json. Exporter: 03_Code/05_Prototype/export_discovery_shoppers.py. Next: review the actual page, then test whether the new row is understandable and useful; no further model tuning on exposed audit answers.

## Discovery photos — 24 October 2026

All displayed A/B discovery products now have embedded photos. Trail Mix, Clementines and granola bars use illustrative stock photography; Soda reuses its existing photo. These aren't verified exact brand packaging. Sources and license links are in Assets/prototype_image_sources.json. Discovery still shows three products, matching the evaluated top-three scope. Five is technically possible but needs a separately documented scope/evaluation change; current @3 results don't describe five suggestions.

## Current UI: five discovery products — 24 October 2026

Justin requested five discovery cards. The illustrative A/B export now takes the top five from the unchanged similarity ranking; each has five unfamiliar products, all from related-product scoring, with no popularity-fill slots. C retains its popular fallback. All new cards have embedded illustrative photos, including Pub Mix and Apples. Add/remove and original study suppression passed stub-DOM checks. No browser visual review or discovery user study is claimed.

**Evidence boundary:** original development and reserved metrics remain @3. The five-card presentation is a subsequent UI scope change, not a newly validated @5 method. No evaluation scripts, frozen models, protocols or scores were changed or rerun. Audit answers remain exposed; don't imply a fresh five-item audit. Claude's portfolio copy is unchanged.

A: Trail Mix, Clementines, Crunchy Oats 'n Honey Granola Bars, Pub Mix, Apples. B: Trail Mix, Soda, Clementines, Crunchy Oats 'n Honey Granola Bars, Zero Calorie Cola. Three of five overlap. See the Learning notes for the traced explanation and limitations.
