"""Offline check: build both GUI models, serialize them, and apply a drill-down.

Runs without the agent, the websocket server, or an LLM call.
"""
import json
import os

# Optional local shim, used when `baf` is installed from a different checkout or
# the machine's TLS trust store is needed. Absent in a normal setup.
try:
    import _bootstrap  # noqa: F401  -- must be imported before baf
except ImportError:
    pass

import analytics
import gui_builder
from analytics import Filters
from baf.core.gui.gui_serializer import gui_to_json

HERE = os.path.dirname(os.path.abspath(__file__))

text = open(os.path.join(HERE, 'nova_sales_2026.csv'), encoding='utf-8').read()
df = analytics.load_csv(text)
print(f'rows={len(df)} columns={list(df.columns)}')

stats = analytics.compute(df, Filters())
print('revenue   ', f"${stats['revenue']:,.0f}")
print('by_region ', stats['by_region'])
print('top reps  ', [r['rep'] for r in stats['reps']][:3])

upload = gui_builder.build_upload_gui()
up_json = json.loads(gui_to_json(upload))
print('\nupload screen OK, bytes =', len(json.dumps(up_json)))

gui = gui_builder.build_dashboard_gui(
    stats,
    regions=analytics.options(df, 'region'),
    channels=analytics.options(df, 'channel'),
)
gui_builder.refresh_dashboard(gui, stats, Filters())
dash = json.loads(gui_to_json(gui))
print('dashboard OK, bytes =', len(json.dumps(dash)))


def walk(elements, depth=0):
    for el in sorted(elements, key=lambda e: (e.get('display_order', 99), e['name'])):
        tag = el.get('component_id') or el['name']
        print('  ' * depth + f"- {el['type']:<14} {tag}")
        walk(el.get('view_elements', []), depth + 1)


screen = dash['modules'][0]['screens'][0]
print('\nComponent tree:')
walk(screen['view_elements'])

# Every id the agent reacts to must actually exist in the model.
ids = [v for k, v in vars(gui_builder.IDS).items() if not k.startswith('_')]
missing = [i for i in ids if i not in ('csv_upload',) and gui.find_component('component_id', i) is None]
print('\nmissing component ids:', missing or 'none')

# Drill-down: the model is patched in place, values must change.
before = gui.find_component('component_id', gui_builder.IDS.KPI_REVENUE).custom_attributes['data-value']
f = Filters(region='EMEA')
gui_builder.refresh_dashboard(gui, analytics.compute(df, f), f)
after = gui.find_component('component_id', gui_builder.IDS.KPI_REVENUE).custom_attributes['data-value']
scope = gui.find_component('component_id', gui_builder.IDS.SCOPE_LABEL).content
print(f'\nrevenue all={before} -> EMEA={after}  scope={scope!r}')
assert before != after, 'drill-down did not change the KPI'

rows = json.loads(gui.find_component('component_id', gui_builder.IDS.TABLE_REPS)
                  .custom_attributes['data-rows'])
print('EMEA leaderboard:', [r['rep'] for r in rows])
print('\nALL CHECKS PASSED')
