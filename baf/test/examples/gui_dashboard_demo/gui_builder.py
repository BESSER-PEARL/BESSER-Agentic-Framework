"""The B-UML GUI models of the demo: an upload screen and a live analytics dashboard.

Two things are worth noticing here:

* The models are *data-free by construction*. Charts, tables and KPI cards carry their
  runtime values in ``custom_attributes`` -- the same channel the BESSER web editor uses
  for literal chart series. The agent refreshes a dashboard by rewriting those
  attributes on the components it already owns, never by rebuilding the object graph.
* Every component that the agent wants to hear from gets an explicit ``component_id``.
  That id is what comes back inside a ``GUIEvent``, so the ids below are effectively the
  agent's event vocabulary (see ``IDS``).
"""
from __future__ import annotations

import json

from besser.BUML.metamodel.gui import (
    GUIModel, Module, Screen, ViewContainer,
    Button, ButtonType, ButtonActionType,
    Text, InputField, InputFieldType, SelectOption,
    Styling, Size, Position, PositionType, Color, Layout, LayoutType,
)
from besser.BUML.metamodel.gui.dashboard import (
    AgentComponent, BarChart, PieChart, LineChart, Series, Table,
    ExpressionColumn, MetricCard,
)

from baf.core.gui.agent_gui import AgentGUI


# --- Event vocabulary -------------------------------------------------------
# Component ids the agent reacts to. Kept in one place so the agent and the model
# can never drift apart.
class IDS:
    UPLOAD = 'csv_upload'
    SCOPE_LABEL = 'scope_label'
    REGION_FILTER = 'region_filter'
    CHANNEL_FILTER = 'channel_filter'
    RESET = 'reset_btn'
    RESTORE = 'restore_btn'
    KPI_ROW = 'kpi_row'
    KPI_REVENUE = 'kpi_revenue'
    KPI_ORDERS = 'kpi_orders'
    KPI_AVG_DEAL = 'kpi_avg_deal'
    KPI_TOP_CATEGORY = 'kpi_top_category'
    GEN_ROW = 'gen_row'   # container the agent drops generated components into
    CHART_REGION = 'chart_region'
    CHART_CATEGORY = 'chart_category'
    CHART_TREND = 'chart_trend'
    TABLE_REPS = 'table_reps'
    SIDEBAR = 'sidebar'


# --- Palette ----------------------------------------------------------------
INK = '#0f172a'
MUTED = '#64748b'
LINE = '#e2e8f0'
SURFACE = '#ffffff'
CANVAS = '#f1f5f9'
ACCENT = '#4f46e5'

# Categorical palette, ordered so adjacent series stay distinguishable.
SERIES_COLORS = ['#4f46e5', '#0d9488', '#d97706', '#e11d48', '#7c3aed', '#0284c7']


# --- Styling helpers --------------------------------------------------------

def _st(size=None, position=None, color=None, layout=None) -> Styling:
    return Styling(size=size, position=position, color=color, layout=layout)


def _card(flex: str = '1', min_width: str = '0', padding: str = '18px') -> Styling:
    """The shared surface treatment for every panel on the dashboard."""
    return _st(
        size=Size(padding=padding, min_width=min_width),
        color=Color(background_color=SURFACE, border=f'1px solid {LINE}',
                    border_radius='12px', box_shadow='0 1px 2px rgba(15,23,42,0.06)'),
        layout=Layout(layout_type=LayoutType.FLEX, flex_direction='column',
                      gap='10px', flex=flex),
    )


def _row(gap: str = '16px', align: str = 'stretch', justify: str = 'flex-start',
         wrap: str = 'wrap', flex: str | None = None) -> Styling:
    return _st(layout=Layout(layout_type=LayoutType.FLEX, flex_direction='row',
                             gap=gap, align_items=align, justify_content=justify,
                             flex_wrap=wrap, flex=flex))


def _col(gap: str = '16px', flex: str | None = None) -> Styling:
    return _st(layout=Layout(layout_type=LayoutType.FLEX, flex_direction='column',
                             gap=gap, flex=flex))


def _button_style() -> Styling:
    return _st(size=Size(padding='8px 16px', font_size='13px'),
               color=Color(background_color=SURFACE, text_color=INK,
                           border=f'1px solid {LINE}', border_radius='8px'),
               position=Position(cursor='pointer'))


def _text(name, content, size='14px', weight='400', color=INK, order=0, **kw) -> Text:
    return Text(
        name=name, content=content, display_order=order,
        styling=_st(size=Size(font_size=size, font_weight=weight),
                    color=Color(text_color=color)),
        **kw,
    )


# --- Runtime data encoding --------------------------------------------------

DIMMED = '#c7d2fe'


def _series_payload(pairs, name: str, color: str, selected: str = 'All') -> str:
    """Encode one data series the way the chart renderer reads it.

    When *selected* names one of the labels, every other point is dimmed -- the chart
    keeps its full context while showing what the dashboard is currently scoped to.
    """
    def point(label, value):
        p = {'name': label, 'value': value}
        if selected != 'All':
            p['color'] = color if label == selected else DIMMED
        return p

    return json.dumps([{
        'name': name,
        'color': color,
        'data': [point(label, value) for label, value in pairs],
    }])


def _multi_series_payload(pairs, selected: str = 'All') -> str:
    """One colour per slice -- used for the categorical pie chart."""
    return json.dumps([{
        'name': 'Revenue',
        'color': SERIES_COLORS[0],
        'data': [
            {'name': label, 'value': value,
             'color': (SERIES_COLORS[i % len(SERIES_COLORS)]
                       if selected in ('All', label) else DIMMED)}
            for i, (label, value) in enumerate(pairs)
        ],
    }])


# ===========================================================================
# Screen 1 -- upload
# ===========================================================================

def build_upload_gui() -> AgentGUI:
    """Full-page landing screen: drop a CSV, get a dashboard."""
    hero = ViewContainer(
        name='hero', description='Upload panel', display_order=0,
        styling=_st(
            size=Size(padding='44px 48px', max_width='620px', width='100%'),
            color=Color(background_color=SURFACE, border=f'1px solid {LINE}',
                        border_radius='16px', box_shadow='0 10px 30px rgba(15,23,42,0.08)'),
            layout=Layout(layout_type=LayoutType.FLEX, flex_direction='column', gap='14px'),
        ),
        view_elements={
            _text('brand', 'NOVA ANALYTICS', size='12px', weight='700',
                  color=ACCENT, order=0),
            _text('headline', 'Drop in a sales export.', size='30px',
                  weight='700', order=1),
            _text('subhead',
                  'The agent reads your file, builds a dashboard around it, and then '
                  'keeps that dashboard in sync as you explore.',
                  size='15px', color=MUTED, order=2),
            InputField(
                name='csv_upload', description='Sales CSV', component_id=IDS.UPLOAD,
                field_type=InputFieldType.File, label='Sales data (CSV)',
                display_order=3,
                # 'data-send-content' makes the browser ship the file body with the
                # GUIEvent, so the agent can parse it instead of only seeing a name.
                custom_attributes={'data-accept': '.csv,text/csv',
                                   'data-send-content': 'text'},
                styling=_st(size=Size(padding='10px', font_size='14px')),
            ),
            _text('hint',
                  'Expected columns: date, region, category, channel, rep, units, '
                  'unit_price, discount, revenue.',
                  size='12px', color=MUTED, order=4),
        },
    )

    screen = Screen(
        name='Upload', description='Upload a dataset',
        is_main_page=True, screen_size='Large',
        styling=_st(
            size=Size(padding='48px 24px', min_height='100%'),
            color=Color(background_color=CANVAS),
            layout=Layout(layout_type=LayoutType.FLEX, flex_direction='column',
                          align_items='center', justify_content='center', gap='18px'),
        ),
        view_elements={hero},
    )

    model = GUIModel(
        name='NovaAnalyticsUpload', package='com.besser.nova', versionCode='1',
        versionName='1.0', description='Nova Analytics -- data upload',
        modules={Module(name='nova', screens={screen})},
    )
    return AgentGUI(model, gui_id='nova_upload')


# ===========================================================================
# Screen 2 -- dashboard
# ===========================================================================

def _kpi(component_id: str, title: str, order: int, fmt: str = 'number',
         color: str = INK, show_trend: bool = False) -> MetricCard:
    return MetricCard(
        name=component_id, component_id=component_id, metric_title=title,
        format=fmt, value_color=color, show_trend=show_trend, display_order=order,
        styling=_st(
            size=Size(padding='16px 18px', min_width='170px'),
            color=Color(background_color=SURFACE, border=f'1px solid {LINE}',
                        border_radius='12px'),
            layout=Layout(layout_type=LayoutType.FLEX, flex_direction='column',
                          gap='4px', flex='1'),
        ),
        custom_attributes={'data-value': ''},
    )


def _dropdown(component_id: str, label: str, values: list[str], order: int) -> InputField:
    return InputField(
        name=component_id, component_id=component_id, description=label,
        field_type=InputFieldType.Dropdown, label=label, default_value='All',
        display_order=order,
        options=[SelectOption(label=v, value=v) for v in ['All'] + values],
        styling=_st(size=Size(min_width='180px', font_size='13px')),
    )


def build_dashboard_gui(stats: dict, regions: list[str], channels: list[str]) -> AgentGUI:
    """Build the full-page dashboard. Called once; afterwards the agent patches it."""
    header = ViewContainer(
        name='header', description='Dashboard header', display_order=0,
        styling=_row(align='baseline', justify='space-between'),
        view_elements={
            _text('title', 'Nova Analytics', size='22px', weight='700', order=0),
            _text('scope', stats['scope'], size='13px', weight='600',
                  color=ACCENT, order=1, component_id=IDS.SCOPE_LABEL),
        },
    )

    controls = ViewContainer(
        name='controls', description='Filters', display_order=1,
        styling=_row(gap='12px', align='flex-end'),
        view_elements={
            _dropdown(IDS.REGION_FILTER, 'Region', regions, 0),
            _dropdown(IDS.CHANNEL_FILTER, 'Channel', channels, 1),
            Button(
                name='reset', component_id=IDS.RESET, description='Clear all filters',
                label='Reset filters', buttonType=ButtonType.OutlinedButton,
                actionType=ButtonActionType.Filter, display_order=2,
                styling=_button_style(),
            ),
            Button(
                name='restore', component_id=IDS.RESTORE,
                description='Rebuild the dashboard as first generated',
                label='Restore layout', buttonType=ButtonType.OutlinedButton,
                actionType=ButtonActionType.RunMethod, display_order=3,
                styling=_button_style(),
            ),
        },
    )

    kpis = ViewContainer(
        name='kpis', description='Key metrics', component_id=IDS.KPI_ROW,
        display_order=2, styling=_row(gap='12px'),
        view_elements={
            _kpi(IDS.KPI_REVENUE, 'Revenue', 0, fmt='currency', color=ACCENT),
            _kpi(IDS.KPI_ORDERS, 'Orders', 1),
            _kpi(IDS.KPI_AVG_DEAL, 'Avg deal size', 2, fmt='currency', show_trend=True),
            _kpi(IDS.KPI_TOP_CATEGORY, 'Top category', 3),
        },
    )

    chart_region = BarChart(
        name='revenue_by_region', component_id=IDS.CHART_REGION,
        title='Revenue by region', orientation='vertical', show_legend=False,
        display_order=0, series=[Series('Revenue', 'Revenue', None, None)],
        styling=_st(size=Size(width='100%', min_height='300px')),
        custom_attributes={'series': _series_payload(stats['by_region'], 'Revenue',
                                                     SERIES_COLORS[0])},
    )

    chart_category = PieChart(
        name='revenue_by_category', component_id=IDS.CHART_CATEGORY,
        title='Revenue by category', show_legend=True, inner_radius=55,
        display_order=0, series=[Series('Revenue', 'Revenue', None, None)],
        styling=_st(size=Size(width='100%', min_height='300px')),
        custom_attributes={'series': _multi_series_payload(stats['by_category'])},
    )

    chart_trend = LineChart(
        name='monthly_trend', component_id=IDS.CHART_TREND,
        title='Monthly revenue', curve_type='monotone', show_legend=False,
        display_order=4, series=[Series('Revenue', 'Revenue', None, None)],
        styling=_st(size=Size(width='100%', min_height='280px')),
        custom_attributes={'series': _series_payload(stats['trend'], 'Revenue',
                                                     SERIES_COLORS[1])},
    )

    charts_row = ViewContainer(
        name='charts', description='Breakdowns', component_id='charts_row',
        display_order=3, styling=_row(gap='16px'),
        view_elements={
            ViewContainer(name='region_card', description='Region panel',
                          component_id='region_card',
                          display_order=0, styling=_card(min_width='320px'),
                          view_elements={chart_region}),
            ViewContainer(name='category_card', description='Category panel',
                          component_id='category_card',
                          display_order=1, styling=_card(min_width='320px'),
                          view_elements={chart_category}),
        },
    )

    trend_card = ViewContainer(
        name='trend_card', description='Trend panel', component_id='trend_card',
        display_order=4, styling=_card(), view_elements={chart_trend},
    )

    table = Table(
        name='top_reps', component_id=IDS.TABLE_REPS, title='Top performers',
        show_header=True, striped_rows=True, rows_per_page=8, display_order=0,
        columns=[
            ExpressionColumn('Rep', 'rep'),
            ExpressionColumn('Revenue', 'revenue'),
            ExpressionColumn('Orders', 'orders'),
            ExpressionColumn('Avg deal', 'avg_deal'),
        ],
        custom_attributes={'data-rows': json.dumps(stats['reps'])},
    )

    table_card = ViewContainer(
        name='table_card', description='Leaderboard panel', component_id='table_card',
        display_order=6, styling=_card(), view_elements={table},
    )

    # Starts empty. Anything the agent generates at run time lands here, so a new
    # chart has a well-defined home without disturbing the authored layout.
    gen_row = ViewContainer(
        name='generated', description='Agent-generated components',
        component_id=IDS.GEN_ROW, display_order=5, styling=_row(gap='16px'),
        view_elements=set(),
    )

    main_column = ViewContainer(
        name='main', description='Dashboard column', display_order=0,
        styling=_col(gap='16px', flex='1 1 640px'),
        view_elements={header, controls, kpis, charts_row, trend_card, gen_row,
                       table_card},
    )

    sidebar = ViewContainer(
        name='sidebar', description='Conversation panel', component_id=IDS.SIDEBAR,
        display_order=1,
        styling=_st(
            # Sticky so the conversation stays put while the dashboard scrolls, and
            # sized to the viewport so the chat always fills its panel.
            size=Size(width='430px', min_width='380px', height='calc(100vh - 116px)'),
            position=Position(p_type=PositionType.STICKY, top='24px'),
            layout=Layout(layout_type=LayoutType.FLEX, flex_direction='column',
                          gap='10px', flex='0 0 430px'),
        ),
        view_elements={
            AgentComponent(
                name='assistant', agent_title='Ask about this data',
                component_id='assistant_dash', display_order=0,
                styling=_st(size=Size(width='100%', height='100%')),
            ),
        },
    )

    screen = Screen(
        name='Dashboard', description='Live sales dashboard',
        is_main_page=True, screen_size='Large',
        styling=_st(
            size=Size(padding='24px'),
            color=Color(background_color=CANVAS),
            layout=Layout(layout_type=LayoutType.FLEX, flex_direction='row',
                          gap='20px', align_items='flex-start', flex_wrap='wrap'),
        ),
        view_elements={main_column, sidebar},
    )

    model = GUIModel(
        name='NovaAnalyticsDashboard', package='com.besser.nova', versionCode='1',
        versionName='1.0', description='Nova Analytics -- live dashboard',
        modules={Module(name='nova', screens={screen})},
    )
    return AgentGUI(model, gui_id='nova_dashboard')


# ===========================================================================
# Incremental refresh
# ===========================================================================

def refresh_dashboard(gui: AgentGUI, stats: dict, filters, df=None) -> None:
    """Patch the live dashboard in place with a newly computed slice.

    Only ``custom_attributes`` and a label change -- the object graph is untouched,
    which is the whole point of GUI Mode's incremental updates.
    """
    gui.update_component_by_id(IDS.SCOPE_LABEL, content=stats['scope'])

    gui.update_component_by_id(IDS.KPI_REVENUE, custom_attributes={
        'data-value': str(stats['revenue']),
        'data-caption': f"{stats['share']}% of total",
    })
    gui.update_component_by_id(IDS.KPI_ORDERS, custom_attributes={
        'data-value': str(stats['orders']),
        'data-caption': f"{stats['units']:,} units",
    })
    gui.update_component_by_id(IDS.KPI_AVG_DEAL, custom_attributes={
        'data-value': str(stats['avg_deal']),
        'data-delta': str(stats['avg_delta']),
        'data-caption': 'vs. dataset average',
    })
    gui.update_component_by_id(IDS.KPI_TOP_CATEGORY, custom_attributes={
        'data-value': stats['top_category'],
        'data-caption': 'by revenue',
    })

    gui.update_component_by_id(IDS.CHART_REGION, custom_attributes={
        'series': _series_payload(stats['by_region'], 'Revenue', SERIES_COLORS[0],
                                  selected=filters.region),
    })
    gui.update_component_by_id(IDS.CHART_CATEGORY, custom_attributes={
        'series': _multi_series_payload(stats['by_category'], selected=filters.category),
    })
    gui.update_component_by_id(IDS.CHART_TREND, custom_attributes={
        'series': _series_payload(stats['trend'], 'Revenue', SERIES_COLORS[1]),
    })
    gui.update_component_by_id(IDS.TABLE_REPS, custom_attributes={
        'data-rows': json.dumps(stats['reps']),
    })

    # Keep the dropdowns showing what the agent currently believes is selected,
    # whichever control (or chart click) set it.
    gui.update_component_by_id(IDS.REGION_FILTER, default_value=filters.region)
    gui.update_component_by_id(IDS.CHANNEL_FILTER, default_value=filters.channel)

    refresh_generated(gui, df, filters, stats)


# ===========================================================================
# Agent-generated components
# ===========================================================================
#
# A generated component declares what it is bound to in its own
# ``custom_attributes`` -- ``data-bind-dimension`` for a chart, ``data-bind-metric``
# for a KPI. Nothing else needs a registry: ``refresh_generated`` walks the live
# model, reads those declarations back off the objects, and recomputes from the
# dataframe. That is what keeps a generated component showing *real* numbers that
# track the current scope, instead of whatever the LLM imagined.

CHART_CLASSES = {'BarChart': BarChart, 'PieChart': PieChart, 'LineChart': LineChart}


def walk(gui: AgentGUI):
    """Yield every element in the model, depth first."""
    def rec(elements):
        for el in elements:
            yield el
            yield from rec(getattr(el, 'view_elements', None) or [])

    screen = gui.get_screen()
    yield from rec(screen.view_elements if screen else [])


def make_chart(component_id: str, chart_type: str, dimension: str, title: str,
               pairs, color_index: int = 2):
    """Build a data-bound chart of the requested type."""
    cls = CHART_CLASSES.get(chart_type, BarChart)
    color = SERIES_COLORS[color_index % len(SERIES_COLORS)]
    kwargs = dict(
        name=component_id, component_id=component_id, title=title,
        display_order=0, series=[Series('Revenue', 'Revenue', None, None)],
        styling=_st(size=Size(width='100%', min_height='300px')),
        custom_attributes={
            'series': (_multi_series_payload(pairs) if cls is PieChart
                       else _series_payload(pairs, 'Revenue', color)),
            # The binding travels with the component, so refresh needs no registry.
            'data-bind-dimension': dimension,
            'data-bind-color': str(color_index),
        },
    )
    if cls is PieChart:
        kwargs['inner_radius'] = 55
    else:
        kwargs['show_legend'] = False
    return cls(**kwargs)


def make_kpi(component_id: str, metric: str, title: str, value, fmt: str,
             caption: str, month=None) -> MetricCard:
    """Build a data-bound KPI card, optionally scoped to a single month."""
    bindings = {'data-bind-metric': metric}
    if month:
        bindings['data-bind-month'] = str(month)
    return MetricCard(
        name=component_id, component_id=component_id, metric_title=title,
        format=fmt, value_color=ACCENT, show_trend=False, display_order=0,
        styling=_st(
            size=Size(padding='16px 18px', min_width='170px'),
            color=Color(background_color=SURFACE,
                        border=f'2px dashed {ACCENT}', border_radius='12px'),
            layout=Layout(layout_type=LayoutType.FLEX, flex_direction='column',
                          gap='4px', flex='1'),
        ),
        custom_attributes={'data-value': str(value), 'data-caption': caption,
                           **bindings},
    )


def wrap_in_card(component, component_id: str) -> ViewContainer:
    """Give a generated chart the same surface treatment as the authored panels."""
    return ViewContainer(
        name=f'{component_id}_card', description='Generated panel',
        component_id=f'{component_id}_card', display_order=0,
        styling=_card(min_width='320px'), view_elements={component},
    )


def refresh_generated(gui: AgentGUI, df, filters, stats: dict) -> None:
    """Recompute every component that declares a data binding."""
    if df is None:
        return
    import analytics

    for el in list(walk(gui)):
        attrs = getattr(el, 'custom_attributes', None) or {}

        dimension = attrs.get('data-bind-dimension')
        if dimension:
            pairs = analytics.by_dimension(df, filters, dimension)
            color = SERIES_COLORS[int(attrs.get('data-bind-color', 2)) % len(SERIES_COLORS)]
            payload = (_multi_series_payload(pairs) if isinstance(el, PieChart)
                       else _series_payload(pairs, 'Revenue', color))
            el.custom_attributes = {**attrs, 'series': payload}
            continue

        metric = attrs.get('data-bind-metric')
        if metric:
            month = attrs.get('data-bind-month')
            value = analytics.metric_value(df, filters, metric, month)
            caption = f"{month} · {stats['scope']}" if month else f"generated · {stats['scope']}"
            el.custom_attributes = {**attrs, 'data-value': str(value),
                                    'data-caption': caption}
