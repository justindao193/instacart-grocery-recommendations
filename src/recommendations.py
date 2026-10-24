"""Portable reference for the selected ranking rules, not the historical evaluator.

Uses only Python's standard library. Order numbers are positions, not dates.
The full-data implementation and its frozen evidence remain in the stage folders.
"""
from collections import defaultdict
from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Iterable, Mapping


@dataclass(frozen=True)
class Purchase:
    """One product in one earlier order; this isn't a purchase quantity."""
    product_id: int
    order_number: int


@dataclass(frozen=True)
class RankedProduct:
    product_id: int
    score: float
    last_order: int


def _earlier(history: Iterable[Purchase], cutoff: int) -> set[Purchase]:
    """Apply the time boundary before calculating any personal clues."""
    if cutoff < 0:
        raise ValueError("cutoff must be zero or a positive order position")
    rows = set(history)  # Count each product only once per order.
    if any(row.order_number < 1 for row in rows):
        raise ValueError("purchase order positions must start at one")
    return {row for row in rows if row.order_number <= cutoff}


def weighted_history(history: Iterable[Purchase], cutoff: int) -> list[RankedProduct]:
    """Add earlier purchases; a purchase five order positions older is worth half.

    Return every familiar candidate so hiding can happen before top-five selection.
    Round to twelve decimals, then break ties by last purchase and product ID.
    """
    scores: dict[int, float] = defaultdict(float)
    latest: dict[int, int] = {}
    for row in sorted(_earlier(history, cutoff), key=lambda r: (r.order_number, r.product_id)):
        scores[row.product_id] += 0.5 ** ((cutoff - row.order_number) / 5.0)
        latest[row.product_id] = max(latest.get(row.product_id, 0), row.order_number)
    ranked = [RankedProduct(pid, round(score, 12), latest[pid]) for pid, score in scores.items()]
    return sorted(ranked, key=lambda r: (-r.score, -r.last_order, r.product_id))


def familiar_products(history: Iterable[Purchase], cutoff: int, *,
                      hidden: Iterable[int] = (), popularity: Iterable[int] = (),
                      k: int = 5) -> list[int]:
    """Select familiar products after hiding; use popularity only for no history."""
    if k < 1:
        raise ValueError("k must be positive")
    ranked = weighted_history(history, cutoff)
    if not ranked:
        return list(dict.fromkeys(popularity))[:k]
    excluded = set(hidden)
    # A short personal list stays short. Hiding everything mustn't insert filler.
    return [r.product_id for r in ranked if r.product_id not in excluded][:k]


def build_connections(histories: Iterable[Iterable[int]], *, min_buyers: int = 50,
                      min_shared: int = 5, max_neighbours: int = 40
                      ) -> dict[int, list[tuple[int, float]]]:
    """Build shared-buyer cosine links from eligible earlier histories only.

    One input row is one shopper's set of products. Caller owns cohort and cutoff
    selection. This readable pairwise version is for small examples; the historical
    implementation uses sparse matrices to handle the full dataset efficiently.
    """
    if min(min_buyers, min_shared, max_neighbours) < 1:
        raise ValueError("support and neighbour limits must be positive")
    buyers: dict[int, set[int]] = defaultdict(set)
    for user, products in enumerate(histories):
        for pid in set(products):
            buyers[pid].add(user)
    eligible = sorted(pid for pid, users in buyers.items() if len(users) >= min_buyers)
    neighbours: dict[int, list[tuple[int, float]]] = {pid: [] for pid in eligible}
    for i, left in enumerate(eligible):
        for right in eligible[i + 1:]:
            shared = len(buyers[left] & buyers[right])
            if shared < min_shared:
                continue
            # Divide by popularity support so shared-buyer count isn't the only clue.
            similarity = shared / sqrt(len(buyers[left]) * len(buyers[right]))
            neighbours[left].append((right, similarity))
            neighbours[right].append((left, similarity))
    return {pid: sorted(rows, key=lambda r: (-round(r[1], 12), r[0]))[:max_neighbours]
            for pid, rows in neighbours.items()}


def discovery_products(history: Iterable[Purchase], cutoff: int,
                       neighbours: Mapping[int, Iterable[tuple[int, float]]],
                       popularity: Iterable[int], *, k: int = 5) -> list[int]:
    """Weight connections by ten recent-history seeds; exclude all familiar items.

    Scores are ranking points, not purchase probabilities. Popularity fills gaps
    only after unfamiliar related products have been ranked.
    """
    if k < 1:
        raise ValueError("k must be positive")
    ranked = weighted_history(history, cutoff)
    seen = {row.product_id for row in ranked}
    scores: dict[int, float] = defaultdict(float)
    for seed in ranked[:10]:
        for candidate, similarity in neighbours.get(seed.product_id, ()):
            if not isfinite(similarity) or not 0 <= similarity <= 1:
                raise ValueError("cosine similarity must be between zero and one")
            if candidate not in seen and similarity > 0:
                scores[candidate] += seed.score * similarity
    selected = sorted(scores, key=lambda pid: (-round(scores[pid], 12), pid))[:k]
    for pid in popularity:
        if len(selected) >= k:
            break
        if pid not in seen and pid not in selected:
            selected.append(pid)
    return selected


def basket_metrics(suggestions: Iterable[int], actual: Iterable[int], *, k: int = 5
                   ) -> dict[str, float]:
    """Measure one shopper; average shopper-level values for a cohort result.

    Precision divides by k even for short lists. Recall uses the whole actual
    basket, including products that weren't available as familiar candidates.
    """
    predicted, target = list(suggestions), set(actual)
    if k < 1 or len(predicted) > k or len(predicted) != len(set(predicted)):
        raise ValueError("suggestions must be unique and contain at most k products")
    if not target:
        raise ValueError("a known nonempty target basket is required")
    matches = len(set(predicted) & target)
    return {"precision": matches / k, "recall": matches / len(target),
            "hit": float(matches > 0)}
