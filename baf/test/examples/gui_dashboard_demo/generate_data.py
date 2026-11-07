"""Generate the synthetic sales dataset used by the GUI dashboard demo.

Run once: ``python generate_data.py`` -> writes ``nova_sales_2026.csv`` next to this file.
The numbers are fabricated but shaped so the dashboard tells a story: EMEA leads on
revenue, Direct beats Partner on deal size, and Q4 shows a clear seasonal lift.
"""
import csv
import os
import random
from datetime import date, timedelta

SEED = 20261106
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nova_sales_2026.csv')

REGIONS = {
    # region: (relative weight, revenue multiplier)
    'EMEA': (0.34, 1.25),
    'North America': (0.30, 1.15),
    'APAC': (0.22, 0.95),
    'LATAM': (0.14, 0.75),
}

CATEGORIES = {
    # category: (relative weight, unit price range)
    'Platform License': (0.26, (1800, 4200)),
    'Analytics Add-on': (0.22, (600, 1600)),
    'Support Plan': (0.20, (300, 900)),
    'Professional Services': (0.18, (1200, 3000)),
    'Training': (0.14, (200, 700)),
}

CHANNELS = {'Direct': (0.58, 1.18), 'Partner': (0.42, 0.86)}

REPS = [
    'A. Moreau', 'B. Keller', 'C. Okafor', 'D. Lindqvist', 'E. Navarro',
    'F. Tanaka', 'G. Haddad', 'H. Petrov', 'I. Ferreira', 'J. Nowak',
    'K. Mensah', 'L. Rossi',
]

# Monthly seasonality: slow summer, strong Q4 close.
MONTH_FACTOR = [0.82, 0.88, 1.05, 0.98, 1.02, 1.10, 0.74, 0.70, 1.08, 1.15, 1.22, 1.45]


def weighted_choice(rng, table):
    """Pick a key from {key: (weight, ...)} proportionally to its weight."""
    keys = list(table)
    weights = [table[k][0] for k in keys]
    return rng.choices(keys, weights=weights, k=1)[0]


def main():
    rng = random.Random(SEED)
    start = date(2026, 1, 1)
    rows = []

    for i in range(900):
        day = start + timedelta(days=rng.randrange(365))
        region = weighted_choice(rng, REGIONS)
        category = weighted_choice(rng, CATEGORIES)
        channel = weighted_choice(rng, CHANNELS)

        # Reps are regionally clustered, so drilling into a region changes the leaderboard.
        rep_pool = REPS[list(REGIONS).index(region) * 3:][:5] or REPS
        rep = rng.choice(rep_pool)

        lo, hi = CATEGORIES[category][1]
        unit_price = round(rng.uniform(lo, hi), 2)
        units = rng.randint(1, 14)
        seasonal = MONTH_FACTOR[day.month - 1]
        multiplier = REGIONS[region][1] * CHANNELS[channel][1] * seasonal
        discount = round(rng.choice([0, 0, 0, 0.05, 0.1, 0.15]), 2)

        revenue = round(units * unit_price * multiplier * (1 - discount), 2)

        rows.append({
            'order_id': f'NR-{26000 + i}',
            'date': day.isoformat(),
            'region': region,
            'category': category,
            'channel': channel,
            'rep': rep,
            'units': units,
            'unit_price': unit_price,
            'discount': discount,
            'revenue': revenue,
        })

    rows.sort(key=lambda r: r['date'])

    with open(OUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    total = sum(r['revenue'] for r in rows)
    print(f'Wrote {len(rows)} rows to {OUT}')
    print(f'Total revenue: {total:,.0f}')


if __name__ == '__main__':
    main()
