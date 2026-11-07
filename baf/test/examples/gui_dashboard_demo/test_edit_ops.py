"""Offline check of the GUI-model edit operations, with no agent and no LLM.

Feeds hand-written edit plans straight into the agent's `_apply_operation` and
asserts the live model really changed: components added, chart classes swapped,
components removed, and generated components rebinding to the current scope.
"""
import json
import os

# Optional local shim, used when `baf` is installed from a different checkout or
# the machine's TLS trust store is needed. Absent in a normal setup.
try:
    import _bootstrap  # noqa: F401  -- must be imported before baf
except ImportError:
    pass

from besser.BUML.metamodel.gui.dashboard import BarChart, PieChart, MetricCard

import analytics
import gui_builder
from analytics import Filters
from gui_builder import IDS

HERE = os.path.dirname(os.path.abspath(__file__))


class FakeSession:
    """Just enough Session for `_apply_operation`: a GUI, a store, and replies."""

    def __init__(self, gui, store):
        self.gui = gui
        self._store = store
        self.replies = []

    def get(self, key, default=None):
        return self._store.get(key, default)

    def set(self, key, value):
        self._store[key] = value

    def set_gui(self, gui):
        self.gui = gui

    def reply(self, text):
        self.replies.append(text)


def ids_in(gui):
    return {getattr(el, 'component_id', None) for el in gui_builder.walk(gui)}


def main():
    import nova_analytics_agent as agent   # imports cleanly without running the server

    text = open(os.path.join(HERE, 'nova_sales_2026.csv'), encoding='utf-8').read()
    df = analytics.load_csv(text)
    filters = Filters()
    stats = analytics.compute(df, filters)

    gui = gui_builder.build_dashboard_gui(
        stats, regions=analytics.options(df, 'region'),
        channels=analytics.options(df, 'channel'))
    gui_builder.refresh_dashboard(gui, stats, filters, df=df)

    session = FakeSession(gui, {'df': df, 'filters': filters, 'stats': stats})

    def apply(op):
        out = agent._apply_operation(session, op)
        print(f'  {op["op"]:<14} -> {out}')
        return out

    # --- add a chart on a dimension the dashboard never had ----------------
    print('\nadd_chart (channel, BarChart)')
    assert apply({'op': 'add_chart', 'chart_type': 'BarChart',
                  'dimension': 'channel', 'title': 'Revenue by channel'})
    chart = gui.find_component('component_id', 'gen_revenue_by_channel')
    assert isinstance(chart, BarChart), type(chart)
    series = json.loads(chart.custom_attributes['series'])[0]['data']
    by_channel = dict(analytics.by_dimension(df, filters, 'channel'))
    assert {p['name']: p['value'] for p in series} == by_channel, 'chart data is not real'
    print(f'    real data: {by_channel}')

    # --- change an existing chart's type -----------------------------------
    print('\nreplace_chart (category pie -> bar)')
    assert isinstance(gui.find_component('component_id', IDS.CHART_CATEGORY), PieChart)
    assert apply({'op': 'replace_chart', 'target': IDS.CHART_CATEGORY,
                  'chart_type': 'BarChart'})
    swapped = gui.find_component('component_id', IDS.CHART_CATEGORY)
    assert isinstance(swapped, BarChart), type(swapped)
    assert swapped.owner is not None and swapped.owner.name == 'category_card'
    print(f'    {IDS.CHART_CATEGORY} is now {type(swapped).__name__}, still in '
          f'{swapped.owner.name}')

    # --- add a KPI bound to a real metric ----------------------------------
    print('\nadd_kpi (avg_deal)')
    assert apply({'op': 'add_kpi', 'metric': 'avg_deal', 'title': 'Avg deal'})
    kpi = gui.find_component('component_id', 'kpi_avg_deal_1') or \
        gui.find_component('component_id', 'kpi_avg_deal')
    card = [el for el in gui_builder.walk(gui)
            if isinstance(el, MetricCard)
            and (el.custom_attributes or {}).get('data-bind-metric') == 'avg_deal'][0]
    assert float(card.custom_attributes['data-value']) == stats['avg_deal']
    print(f"    value {card.custom_attributes['data-value']} == stats avg_deal")

    # --- generated components follow the scope -----------------------------
    print('\nrebind after drilling into EMEA')
    emea = Filters(region='EMEA')
    session.set('filters', emea)
    emea_stats = analytics.compute(df, emea)
    session.set('stats', emea_stats)
    gui_builder.refresh_dashboard(gui, emea_stats, emea, df=df)

    assert float(card.custom_attributes['data-value']) == emea_stats['avg_deal']
    new_series = json.loads(chart.custom_attributes['series'])[0]['data']
    emea_channel = dict(analytics.by_dimension(df, emea, 'channel'))
    assert {p['name']: p['value'] for p in new_series} == emea_channel
    assert emea_channel != by_channel, 'generated chart did not follow the drill-down'
    print(f"    KPI {card.custom_attributes['data-value']}, chart {emea_channel}")

    # --- remove, including the empty card wrapper --------------------------
    print('\nremove (the generated chart)')
    before = ids_in(gui)
    assert apply({'op': 'remove', 'target': 'gen_revenue_by_channel'})
    after = ids_in(gui)
    assert 'gen_revenue_by_channel' not in after
    assert 'gen_revenue_by_channel_card' not in after, 'empty wrapper left behind'
    print(f'    dropped {sorted(before - after)}')

    # --- retitle ------------------------------------------------------------
    print('\nretitle')
    assert apply({'op': 'retitle', 'target': IDS.CHART_TREND, 'title': 'Monthly run rate'})
    assert gui.find_component('component_id', IDS.CHART_TREND).title == 'Monthly run rate'

    # --- a bad plan must not corrupt the model ------------------------------
    print('\nrejected operations')
    assert apply({'op': 'remove', 'target': 'does_not_exist'}) is None
    assert apply({'op': 'add_chart', 'dimension': 'nonsense'}) is None
    assert apply({'op': 'add_kpi', 'metric': 'nonsense'}) is None

    # --- re-adding the same chart must replace it, not collide -------------
    print('\nre-adding the same chart twice')
    op = {'op': 'add_chart', 'chart_type': 'PieChart', 'dimension': 'category',
          'title': 'Revenue by category'}
    assert apply(op)
    assert apply(op), 'second add raised or was rejected'
    cards = [el for el in gui_builder.walk(gui)
             if getattr(el, 'component_id', '') == 'gen_revenue_by_category_card']
    assert len(cards) == 1, f'{len(cards)} duplicate wrappers left behind'
    print('    exactly one wrapper survives')

    # --- a month-scoped KPI must carry the real November figure ------------
    print('\nadd_kpi scoped to November')
    assert apply({'op': 'add_kpi', 'metric': 'revenue', 'month': 'November',
                  'title': 'November revenue'})
    nov = [el for el in gui_builder.walk(gui)
           if (getattr(el, 'custom_attributes', None) or {}).get('data-bind-month')][0]
    shown = float(nov.custom_attributes['data-value'])
    expected = analytics.metric_value(df, session.get('filters'), 'revenue', 'Nov')
    assert shown == expected and shown > 0, (shown, expected)
    print(f'    shows ${shown:,.0f}, matches the dataframe')

    # and it must follow the scope like everything else
    gui_builder.refresh_dashboard(gui, analytics.compute(df, Filters()), Filters(), df=df)
    unscoped = float(nov.custom_attributes['data-value'])
    assert unscoped == analytics.metric_value(df, Filters(), 'revenue', 'Nov')
    assert unscoped != shown, 'month KPI ignored the scope change'
    print(f'    rebinds to ${unscoped:,.0f} once the EMEA filter is cleared')

    # --- the restore button's id must exist on the model -------------------
    assert gui.find_component('component_id', IDS.RESTORE) is not None
    print(f'\nrestore button present: {IDS.RESTORE}')

    # --- the model still serializes ----------------------------------------
    from baf.core.gui.gui_serializer import gui_to_json
    print(f'\nmodel still serializes: {len(gui_to_json(gui))} bytes')

    print('\nALL EDIT-OP CHECKS PASSED')


if __name__ == '__main__':
    main()
