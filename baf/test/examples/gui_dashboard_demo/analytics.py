"""Dataset loading and aggregation for the GUI dashboard demo.

Pure data work: everything here returns plain Python values, so the GUI builder and
the agent never touch pandas directly.
"""
from __future__ import annotations

import io

import pandas as pd

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

#: Columns the dashboard can group by, and the label shown for each.
DIMENSIONS = {
    'region': 'Region',
    'category': 'Category',
    'channel': 'Channel',
    'rep': 'Rep',
    'month': 'Month',
}

#: Columns that can be filtered on, and how a filter widget should capture them.
FILTERABLE = {
    'region': 'categorical',
    'category': 'categorical',
    'channel': 'categorical',
    'rep': 'categorical',
    'date': 'date',
    'revenue': 'numeric',
    'units': 'numeric',
    'unit_price': 'numeric',
    'discount': 'numeric',
}

#: Scalar metrics a KPI card can show, and how to read them out of a stats dict.
METRICS = {
    'revenue': ('Revenue', 'currency'),
    'orders': ('Orders', 'number'),
    'units': ('Units', 'number'),
    'avg_deal': ('Avg deal size', 'currency'),
}


def load_csv(text: str) -> pd.DataFrame:
    """Parse an uploaded CSV into the dataframe the dashboard expects."""
    df = pd.read_csv(io.StringIO(text))
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month
    return df


class Filters:
    """The dashboard's current scope.

    Categorical filters live in a dict keyed by column name, so a form the agent
    generated at run time can introduce a filter the dashboard never knew about.
    ``region`` / ``channel`` / ``category`` keep named properties because the
    built-in dashboard controls refer to them directly.
    """

    def __init__(self, **categorical):
        self.values: dict[str, str] = {k: v for k, v in categorical.items() if v}
        self.date_from: str | None = None
        self.date_to: str | None = None
        self.minimums: dict[str, float] = {}

    # -- named accessors for the three built-in dashboard controls --------
    def _get(self, field: str) -> str:
        return self.values.get(field, 'All')

    region = property(lambda self: self._get('region'),
                      lambda self, v: self.values.__setitem__('region', v))
    channel = property(lambda self: self._get('channel'),
                       lambda self, v: self.values.__setitem__('channel', v))
    category = property(lambda self: self._get('category'),
                        lambda self, v: self.values.__setitem__('category', v))

    def set_field(self, field: str, value) -> None:
        """Set any filter by column name, picking the right slot for its kind."""
        kind = FILTERABLE.get(field)
        if kind == 'date':
            if isinstance(value, dict):
                self.date_from = value.get('from') or None
                self.date_to = value.get('to') or None
        elif kind == 'numeric':
            try:
                num = float(value)
            except (TypeError, ValueError):
                return
            if num > 0:
                self.minimums[field] = num
            else:
                self.minimums.pop(field, None)
        else:
            self.values[field] = value or 'All'

    def apply(self, df: pd.DataFrame, ignore: str | None = None) -> pd.DataFrame:
        """Filter *df*, optionally leaving one dimension unfiltered.

        A breakdown chart stays readable only if it keeps showing every bar, so the
        'revenue by region' chart is computed with ``ignore='region'`` -- the other
        filters still apply, and the selected bar is merely highlighted.
        """
        out = df
        for field, value in self.values.items():
            if value and value != 'All' and field != ignore and field in out.columns:
                out = out[out[field].astype(str) == value]
        if self.date_from and ignore != 'date':
            out = out[out['date'] >= pd.Timestamp(self.date_from)]
        if self.date_to and ignore != 'date':
            out = out[out['date'] <= pd.Timestamp(self.date_to)]
        for field, minimum in self.minimums.items():
            if field != ignore and field in out.columns:
                out = out[out[field] >= minimum]
        return out

    def is_empty(self) -> bool:
        return not self.active()

    def active(self) -> list[str]:
        """Human-readable list of the filters currently in force."""
        parts = [v for v in self.values.values() if v and v != 'All']
        if self.date_from or self.date_to:
            parts.append(f"{self.date_from or '…'} → {self.date_to or '…'}")
        parts += [f'{f} ≥ {v:,.0f}' for f, v in self.minimums.items()]
        return parts

    def label(self) -> str:
        """Human-readable scope, e.g. 'EMEA · Direct'."""
        parts = self.active()
        return ' · '.join(parts) if parts else 'All regions · All channels'

    def __repr__(self):
        return f'Filters({self.label()})'


def _sum_by(df: pd.DataFrame, column: str) -> list[tuple[str, float]]:
    if df.empty:
        return []
    grouped = df.groupby(column)['revenue'].sum().sort_values(ascending=False)
    return [(str(k), round(float(v), 2)) for k, v in grouped.items()]


def by_dimension(df: pd.DataFrame, filters: Filters, dimension: str,
                 widen: bool = True) -> list[tuple[str, float]]:
    """Revenue aggregated over any dimension, for a chart.

    With *widen* the dimension being plotted is left unfiltered, so the chart keeps
    all of its bars and the selected one can simply be highlighted.
    """
    scoped = filters.apply(df, ignore=dimension if widen else None)
    if dimension == 'month':
        monthly = scoped.groupby('month')['revenue'].sum() if not scoped.empty else None
        return [(MONTHS[m - 1], round(float(monthly.get(m, 0.0)), 2) if monthly is not None else 0.0)
                for m in range(1, 13)]
    if dimension not in scoped.columns:
        return []
    pairs = _sum_by(scoped, dimension)
    # A high-cardinality dimension such as rep is unreadable in full.
    return pairs[:10]


def month_number(name) -> int | None:
    """'Nov', 'november', 11 -> 11. Anything unrecognised -> None."""
    if name is None:
        return None
    if isinstance(name, int) or str(name).isdigit():
        n = int(name)
        return n if 1 <= n <= 12 else None
    key = str(name).strip()[:3].title()
    return MONTHS.index(key) + 1 if key in MONTHS else None


def metric_value(df: pd.DataFrame, filters: Filters, metric: str,
                 month=None) -> float:
    """One scalar metric, optionally narrowed to a single month.

    Lets a KPI card answer "November revenue" with the real figure instead of
    whatever number an LLM would otherwise have made up.
    """
    scoped = filters.apply(df)
    number = month_number(month)
    if number is not None:
        scoped = scoped[scoped['month'] == number]

    revenue = float(scoped['revenue'].sum())
    orders = int(len(scoped))
    return {
        'revenue': round(revenue, 2),
        'orders': orders,
        'units': int(scoped['units'].sum()),
        'avg_deal': round(revenue / orders, 2) if orders else 0.0,
    }.get(metric, 0.0)


def compute(df: pd.DataFrame, filters: Filters) -> dict:
    """Everything the dashboard renders, for the currently filtered slice."""
    scoped = filters.apply(df)

    revenue = float(scoped['revenue'].sum())
    orders = int(len(scoped))
    units = int(scoped['units'].sum())
    avg_deal = revenue / orders if orders else 0.0

    # Trend compares the filtered slice against the same metric over the whole dataset,
    # which is what makes a drill-down immediately readable.
    baseline_avg = float(df['revenue'].mean()) if len(df) else 0.0
    avg_delta = ((avg_deal - baseline_avg) / baseline_avg * 100) if baseline_avg else 0.0
    share = (revenue / float(df['revenue'].sum()) * 100) if len(df) else 0.0

    # Breakdown charts show their full dimension so the user can always click across.
    by_region = by_dimension(df, filters, 'region')
    by_category = by_dimension(df, filters, 'category')
    by_channel = _sum_by(scoped, 'channel')

    scoped_regions = _sum_by(scoped, 'region')
    scoped_categories = _sum_by(scoped, 'category')

    trend = by_dimension(df, filters, 'month', widen=False)

    if scoped.empty:
        reps = []
    else:
        agg = (scoped.groupby('rep')
               .agg(revenue=('revenue', 'sum'), orders=('order_id', 'count'))
               .sort_values('revenue', ascending=False)
               .head(8))
        reps = [
            {
                'rep': str(name),
                'revenue': f"${row.revenue:,.0f}",
                'orders': int(row.orders),
                'avg_deal': f"${row.revenue / row.orders:,.0f}",
            }
            for name, row in agg.iterrows()
        ]

    return {
        'revenue': round(revenue, 2),
        'orders': orders,
        'units': units,
        'avg_deal': round(avg_deal, 2),
        'avg_delta': round(avg_delta, 1),
        'share': round(share, 1),
        'top_category': scoped_categories[0][0] if scoped_categories else '—',
        'top_region': scoped_regions[0][0] if scoped_regions else '—',
        'by_region': by_region,
        'by_category': by_category,
        'by_channel': by_channel,
        'trend': trend,
        'reps': reps,
        'scope': filters.label(),
    }


def options(df: pd.DataFrame, column: str) -> list[str]:
    """Sorted distinct values of a column, for populating a dropdown."""
    return sorted(str(v) for v in df[column].dropna().unique())


def numeric_range(df: pd.DataFrame, column: str) -> tuple[float, float]:
    return float(df[column].min()), float(df[column].max())


def date_range(df: pd.DataFrame) -> tuple[str, str]:
    return df['date'].min().strftime('%Y-%m-%d'), df['date'].max().strftime('%Y-%m-%d')


def summarize_for_llm(df: pd.DataFrame, stats: dict) -> str:
    """A compact factual briefing the chat assistant can reason over."""
    lines = [
        f"Dataset: {len(df)} orders, {df['date'].min():%Y-%m-%d} to {df['date'].max():%Y-%m-%d}.",
        f"Current scope: {stats['scope']}.",
        f"Revenue in scope: ${stats['revenue']:,.0f} ({stats['share']}% of total) "
        f"across {stats['orders']} orders; average deal ${stats['avg_deal']:,.0f}.",
        'Revenue by region: ' + ', '.join(f'{k} ${v:,.0f}' for k, v in stats['by_region']) + '.',
        'Revenue by category: ' + ', '.join(f'{k} ${v:,.0f}' for k, v in stats['by_category']) + '.',
        'Revenue by channel: ' + ', '.join(f'{k} ${v:,.0f}' for k, v in stats['by_channel']) + '.',
        'Monthly revenue: ' + ', '.join(f'{m} ${v:,.0f}' for m, v in stats['trend']) + '.',
    ]
    if stats['reps']:
        lines.append('Top reps: ' + ', '.join(f"{r['rep']} {r['revenue']}" for r in stats['reps'][:5]) + '.')
    return '\n'.join(lines)
