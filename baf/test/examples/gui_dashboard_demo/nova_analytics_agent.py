"""Nova Analytics -- a data-analysis agent that owns its interface.

Demonstrates the three things the paper claims, in one continuous session:

1. **GUI Mode**  -- ``session.set_gui()`` puts a full-page interface on screen and keeps
   it there across turns. The agent patches it in place (``update_component_by_id``)
   rather than rebuilding it, and every click on it arrives as a typed ``GUIEvent``.
2. **GUI Replies** -- ``websocket_platform.reply_gui()`` drops a self-contained form
   into the conversation thread running alongside the dashboard; submitting it fires
   ``when_form_submitted`` and drives a state transition.
3. **LLM-assisted generation** -- ``create_gui_with_llm()`` turns a sentence typed in
   the chat into a schema-validated component, which is then inserted into the live
   dashboard.

Run:
    python baf/test/examples/gui_dashboard_demo/nova_analytics_agent.py

Then in the BESSER agent client, add an agent pointing at ws://localhost:8777 and
pick GUI Mode.
"""
import json
import logging
import os

# Optional local shim, used when `baf` is installed from a different checkout or
# the machine's TLS trust store is needed. Absent in a normal setup.
try:
    import _bootstrap  # noqa: F401  -- must be imported before baf
except ImportError:
    pass

from besser.BUML.metamodel.gui import (
    Alert, Form, InputField, InputFieldType, SelectOption, GUIModel, Module, Screen,
    Text, ViewContainer,
)
from besser.BUML.metamodel.gui.dashboard import MetricCard

from baf.core.agent import Agent
from baf.core.session import Session
from baf.core.gui.agent_gui import AgentGUI
from baf.core.gui.gui_llm import create_gui_with_llm, _extract_json
from baf.exceptions.logger import logger
from baf.library.transition.events.base_events import GUIEvent
from baf.nlp.intent_classifier.intent_classifier_configuration import LLMIntentClassifierConfiguration
from baf.nlp.llm.llm_openai_api import LLMOpenAI
from baf.platforms.websocket import WEBSOCKET_PORT

import analytics
import gui_builder
from analytics import Filters
from gui_builder import IDS

logger.setLevel(logging.INFO)

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, 'config.yaml')

# Id of the GUI Reply form, shared by the sender and the transition that listens for it.
FILTER_FORM_ID = 'nova_filter_form'

LLM_NAME = 'gpt-5.4-mini'

agent = Agent('nova_analytics_agent')
agent.load_properties(CONFIG)
agent.set_property(WEBSOCKET_PORT, 8777)
websocket_platform = agent.use_websocket_platform(use_ui=False)

gpt = LLMOpenAI(agent=agent, name=LLM_NAME, parameters={}, num_previous_messages=10)

agent.set_default_ic_config(LLMIntentClassifierConfiguration(
    llm_name=LLM_NAME,
    parameters={},
    use_intent_descriptions=True,
    use_training_sentences=False,
    use_entity_descriptions=True,
    use_entity_synonyms=False,
))


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def filters_of(session: Session) -> Filters:
    return session.get('filters')


def recompute(session: Session) -> dict:
    """Recompute the current slice and push it into the live dashboard."""
    stats = analytics.compute(session.get('df'), filters_of(session))
    session.set('stats', stats)
    gui_builder.refresh_dashboard(session.gui, stats, filters_of(session),
                                  df=session.get('df'))
    # Re-sending the same AgentGUI is what transmits the patched model to the client.
    session.set_gui(session.gui)
    return stats


# ---------------------------------------------------------------------------
# Intents
# ---------------------------------------------------------------------------

add_widget_intent = agent.new_intent(
    name='add_widget_intent',
    description='The user asks to add, create, build or generate a new element, card, '
                'KPI, metric, chart, panel or widget on the dashboard.',
)

refine_intent = agent.new_intent(
    name='refine_intent',
    description='The user wants to filter, narrow down, slice or change the scope of '
                'the dashboard, or asks to see filtering options.',
)

data_question_intent = agent.new_intent(
    name='data_question_intent',
    description='The user asks a question about the sales data, the numbers, trends, '
                'regions, categories, channels or reps.',
)


# ---------------------------------------------------------------------------
# States
# ---------------------------------------------------------------------------

welcome_state = agent.new_state('welcome_state', initial=True)
awaiting_upload_state = agent.new_state('awaiting_upload_state')
build_dashboard_state = agent.new_state('build_dashboard_state')
dashboard_state = agent.new_state('dashboard_state')
handle_interaction_state = agent.new_state('handle_interaction_state')
answer_state = agent.new_state('answer_state')
generate_widget_state = agent.new_state('generate_widget_state')
offer_filter_state = agent.new_state('offer_filter_state')
apply_filter_state = agent.new_state('apply_filter_state')


# --- 1. Upload screen (GUI Mode) -------------------------------------------

def welcome_body(session: Session):
    # GUI Mode: the agent owns a full-page interface from the very first turn.
    session.set_gui(gui_builder.build_upload_gui())
    session.reply("Hi! Drop a sales CSV above and I'll build you a dashboard.")


welcome_state.set_body(welcome_body)
welcome_state.go_to(awaiting_upload_state)


def is_upload(session: Session) -> bool:
    event = session.event
    return (isinstance(event, GUIEvent)
            and event.event_data.get('elementId') == IDS.UPLOAD
            and isinstance(event.event_data.get('value'), dict))


awaiting_upload_state.when_event(GUIEvent()).with_condition(is_upload).go_to(build_dashboard_state)


# --- 2. Build the dashboard ------------------------------------------------

def install_fresh_dashboard(session: Session) -> dict:
    """Build the authored dashboard from scratch and put it on screen.

    Used both for the first build and for 'Restore layout', which is how the user
    discards every edit the LLM made and returns to the generated starting point.
    """
    df = session.get('df')
    filters = Filters()
    session.set('filters', filters)
    stats = analytics.compute(df, filters)
    session.set('stats', stats)

    gui = gui_builder.build_dashboard_gui(
        stats,
        regions=analytics.options(df, 'region'),
        channels=analytics.options(df, 'channel'),
    )
    gui_builder.refresh_dashboard(gui, stats, filters, df=df)
    session.set_gui(gui)
    return stats


def build_dashboard_body(session: Session):
    payload = session.event.event_data['value']
    df = analytics.load_csv(payload['content'])
    session.set('df', df)

    # A second set_gui() swaps the whole interface: upload screen out, dashboard in.
    stats = install_fresh_dashboard(session)

    session.reply(
        f"Loaded **{payload['filename']}** — {len(df):,} orders, "
        f"${stats['revenue']:,.0f} in revenue.\n\n"
        "Click a bar or a slice to drill in, or just ask me something."
    )


build_dashboard_state.set_body(build_dashboard_body)
build_dashboard_state.go_to(dashboard_state)


# --- 3. The dashboard hub --------------------------------------------------

def dashboard_body(session: Session):
    """Idle hub. Everything interesting happens on the way out of here."""


dashboard_state.set_body(dashboard_body)

# Order matters: transitions are checked in registration order, so the specific
# form-submit matcher has to come before the catch-all GUIEvent transition.
dashboard_state.when_form_submitted(form_id=FILTER_FORM_ID).go_to(apply_filter_state)
dashboard_state.when_event(GUIEvent()).go_to(handle_interaction_state)
dashboard_state.when_intent_matched(add_widget_intent).go_to(generate_widget_state)
dashboard_state.when_intent_matched(refine_intent).go_to(offer_filter_state)
dashboard_state.when_intent_matched(data_question_intent).go_to(answer_state)


# --- 4. Dashboard interactions become agent logic --------------------------

def handle_interaction_body(session: Session):
    """Route one GUIEvent from the dashboard into a filter change."""
    data = session.event.event_data
    element = data.get('elementId')
    action = data.get('action')
    value = data.get('value')
    filters = filters_of(session)

    # A form submission from a GUI Reply is handled by its own transition; and the
    # dashboard may still be mid-swap when a stale event lands.
    if filters is None:
        return

    if element == IDS.RESTORE:
        # Rebuilding from the authored model drops every generated component.
        stats = install_fresh_dashboard(session)
        session.reply(f"Restored the original layout — back to "
                      f"${stats['revenue']:,.0f} across {stats['orders']} orders.")
        return

    if element == IDS.RESET:
        session.set('filters', Filters())
        session.reply('Cleared all filters.')

    elif element == IDS.REGION_FILTER and action == 'onChange':
        filters.region = value or 'All'
        session.reply(f'Region: **{filters.region}**')

    elif element == IDS.CHANNEL_FILTER and action == 'onChange':
        filters.channel = value or 'All'
        session.reply(f'Channel: **{filters.channel}**')

    elif element == IDS.CHART_REGION and action == 'onClick':
        # Clicking the same bar twice zooms back out.
        filters.region = 'All' if filters.region == value else value
        session.reply(f'Drilled into **{filters.region}**.'
                      if filters.region != 'All' else 'Back to all regions.')

    elif element == IDS.CHART_CATEGORY and action == 'onClick':
        filters.category = 'All' if filters.category == value else value
        session.reply(f'Category: **{filters.category}**'
                      if filters.category != 'All' else 'All categories.')

    elif element == IDS.TABLE_REPS and action == 'onRowClick':
        row = value or {}
        session.reply(f"**{row.get('rep')}** — {row.get('revenue')} across "
                      f"{row.get('orders')} orders ({row.get('avg_deal')} average).")
        return  # a row click reports, it does not re-scope the dashboard

    else:
        return

    stats = recompute(session)
    if stats['orders'] == 0:
        session.reply('That combination has no orders — try Reset.')


handle_interaction_state.set_body(handle_interaction_body)
handle_interaction_state.go_to(dashboard_state)


# --- 5. Questions about the data -------------------------------------------

def answer_body(session: Session):
    briefing = analytics.summarize_for_llm(session.get('df'), session.get('stats'))
    answer = gpt.predict(
        'You are a sales analyst reading a live dashboard. Answer the question using '
        'only the figures below. Be concise (2-4 sentences), quote concrete numbers, '
        'and do not invent data.\n\n'
        f'FIGURES\n{briefing}\n\nQUESTION\n{session.event.message}'
    )
    session.reply(answer)


answer_state.set_body(answer_body)
answer_state.go_to(dashboard_state)


# --- 6. LLM-assisted editing of the live GUI model -------------------------
#
# The LLM does not emit the component. It emits an *edit plan* over the model the
# agent already owns -- add / replace / remove / retitle -- and the agent executes
# that plan against the typed object graph, binding real aggregates from the
# dataframe. That is the difference between a KPI card with a plausible-looking
# invented number and one that is actually correct and keeps tracking the scope.
#
# `create_gui_with_llm` still has a job: the `freeform` op, for a component the
# plan vocabulary cannot describe. There, structure is all that is being asked for
# and there is no data to bind, so a generated model is exactly the right answer.

_PLAN_PROMPT = """You edit a live analytics dashboard by emitting a JSON edit plan.

Respond with raw JSON only, no prose and no markdown fences:
{{"operations": [ ... ], "note": "<one short sentence for the user>"}}

Allowed operations:
  {{"op": "add_chart", "chart_type": "BarChart|PieChart|LineChart",
    "dimension": "{dimensions}", "title": "<short title>"}}
  {{"op": "replace_chart", "target": "<component_id>",
    "chart_type": "BarChart|PieChart|LineChart"}}
  {{"op": "add_kpi", "metric": "{metrics}", "title": "<short title>",
    "month": "<optional month name, for a single-month figure>"}}
  {{"op": "remove", "target": "<component_id>"}}
  {{"op": "retitle", "target": "<component_id>", "title": "<new title>"}}
  {{"op": "freeform", "description": "<a text note or callout to display>"}}

Rules:
- "target" must be one of the component ids listed below, exactly.
- Use replace_chart to change a chart's type (pie to bar, etc).
- freeform is for explanatory text or callouts ONLY. Never use it for a chart,
  table or KPI -- those must use add_chart / add_kpi so they get real data.
- Emit the fewest operations that satisfy the request.

Components currently on the dashboard:
{inventory}

Dimensions available for charts: {dimensions}
Metrics available for KPI cards: {metrics}"""


def _inventory(gui) -> str:
    """Describe the live model to the LLM so it can target existing components."""
    lines = []
    for el in gui_builder.walk(gui):
        cid = getattr(el, 'component_id', None)
        if not cid or isinstance(el, ViewContainer):
            continue
        label = (getattr(el, 'title', None) or getattr(el, 'metric_title', None)
                 or getattr(el, 'label', None) or '')
        lines.append(f'  {cid} ({type(el).__name__}){" - " + label if label else ""}')
    return '\n'.join(lines)


def _slug(text: str, prefix: str) -> str:
    base = ''.join(c if c.isalnum() else '_' for c in text.lower()).strip('_')
    return f'{prefix}_{base}'[:40] or prefix


def _drop(gui, component_id: str) -> None:
    """Remove a component *and* its card wrapper.

    A container rejects two children with the same name, so leaving an orphaned
    wrapper behind makes the next insert of the same component fail.
    """
    gui.remove_component(component_id)
    gui.remove_component(f'{component_id}_card')


def _apply_operation(session: Session, op: dict) -> str | None:
    """Execute one edit-plan operation. Returns a description, or None if it failed."""
    gui = session.gui
    df = session.get('df')
    filters = filters_of(session)
    stats = session.get('stats')
    kind = op.get('op')

    if kind == 'add_chart':
        dimension = op.get('dimension')
        if dimension not in analytics.DIMENSIONS:
            return None
        title = op.get('title') or f'Revenue by {analytics.DIMENSIONS[dimension].lower()}'
        cid = _slug(title, 'gen')
        _drop(gui, cid)   # re-adding the same chart replaces it
        pairs = analytics.by_dimension(df, filters, dimension)
        chart = gui_builder.make_chart(cid, op.get('chart_type', 'BarChart'),
                                       dimension, title, pairs)
        gui.add_component(gui_builder.wrap_in_card(chart, cid), parent_id=IDS.GEN_ROW)
        return f'added **{title}**'

    if kind == 'replace_chart':
        target = op.get('target')
        old = gui.find_component('component_id', target)
        if old is None:
            return None
        # A component's class cannot be mutated, so changing a chart's type means
        # building the replacement and swapping it into the same container.
        attrs = getattr(old, 'custom_attributes', None) or {}
        dimension = attrs.get('data-bind-dimension') or _DIMENSION_OF.get(target)
        if dimension is None:
            return None
        parent = getattr(old, 'owner', None)
        parent_id = getattr(parent, 'component_id', None) if parent else None
        title = getattr(old, 'title', None) or 'Revenue'
        pairs = analytics.by_dimension(df, filters, dimension)
        chart = gui_builder.make_chart(target, op.get('chart_type', 'BarChart'),
                                       dimension, title, pairs)
        gui.remove_component(target)
        if parent_id:
            gui.add_component(chart, parent_id=parent_id)
        else:
            gui.add_component(gui_builder.wrap_in_card(chart, target), parent_id=IDS.GEN_ROW)
        return f'turned **{title}** into a {op.get("chart_type", "BarChart")}'

    if kind == 'add_kpi':
        metric = op.get('metric')
        if metric not in analytics.METRICS:
            return None
        # A month-scoped card ("November revenue") is still a real aggregate, not a
        # number the model invented.
        month = analytics.month_number(op.get('month'))
        month_label = analytics.MONTHS[month - 1] if month else None
        default_title, fmt = analytics.METRICS[metric]
        title = op.get('title') or (f'{month_label} {default_title.lower()}'
                                    if month_label else default_title)
        cid = _slug(title, 'kpi')
        _drop(gui, cid)
        value = analytics.metric_value(df, filters, metric, month_label)
        card = gui_builder.make_kpi(
            cid, metric, title, value, fmt,
            f"{month_label} · {stats['scope']}" if month_label
            else f"generated · {stats['scope']}",
            month=month_label)
        gui.add_component(card, parent_id=IDS.KPI_ROW)
        return f'added **{title}**'

    if kind == 'remove':
        target = op.get('target')
        el = gui.find_component('component_id', target)
        if el is None:
            return None
        label = getattr(el, 'title', None) or getattr(el, 'metric_title', None) or target
        # Charts live inside a card wrapper; drop the wrapper so no empty box remains.
        parent = getattr(el, 'owner', None)
        parent_id = getattr(parent, 'component_id', None) if parent else None
        gui.remove_component(target)
        if parent_id and parent_id.endswith('_card') and not parent.view_elements:
            gui.remove_component(parent_id)
        return f'removed **{label}**'

    if kind == 'retitle':
        target = op.get('target')
        el = gui.find_component('component_id', target)
        if el is None or not op.get('title'):
            return None
        if isinstance(el, MetricCard):
            gui.update_component_by_id(target, metric_title=op['title'])
        else:
            gui.update_component_by_id(target, title=op['title'])
        return f'retitled to **{op["title"]}**'

    if kind == 'freeform':
        # Structure with nothing to bind, which is what create_gui_with_llm is for.
        generated = create_gui_with_llm(
            llm=gpt,
            prompt=(f"{op.get('description', '')}\n\n"
                    'Use only Text and Alert elements. No charts, tables or metric '
                    'cards.'))
        screen = generated.get_screen() if generated else None
        if screen is None:
            return None
        # Anything data-bearing would render blank, so keep only annotation elements.
        keep = {el for el in screen.view_elements if isinstance(el, (Text, Alert))}
        if not keep:
            return None
        cid = _slug(op.get('description', 'panel')[:24], 'free')
        _drop(gui, cid)
        panel = ViewContainer(
            name=cid, description='Generated panel', component_id=cid,
            display_order=0, styling=gui_builder._card(min_width='320px'),
            view_elements=keep,
        )
        gui.add_component(panel, parent_id=IDS.GEN_ROW)
        return 'added a note'

    return None


#: Dimensions of the authored charts, so replace_chart works on them too.
_DIMENSION_OF = {
    IDS.CHART_REGION: 'region',
    IDS.CHART_CATEGORY: 'category',
    IDS.CHART_TREND: 'month',
}


def generate_widget_body(session: Session):
    """Let the LLM restructure the live dashboard: add, replace, remove, retitle."""
    session.reply('Working on the dashboard…')

    system = _PLAN_PROMPT.format(
        inventory=_inventory(session.gui),
        dimensions=' | '.join(analytics.DIMENSIONS),
        metrics=' | '.join(analytics.METRICS),
    )
    raw = gpt.predict(session.event.message, system_message=system)

    try:
        plan = json.loads(_extract_json(raw))
        operations = plan.get('operations') or []
    except Exception as exc:
        logger.warning(f'edit plan did not parse: {exc}\n{raw}')
        session.reply("I couldn't turn that into a dashboard change — try rephrasing.")
        return

    logger.info(f'edit plan: {operations}')
    done = [d for d in (_apply_operation(session, op) for op in operations) if d]

    if not done:
        session.reply("I couldn't apply that to the dashboard — try naming the "
                      "chart or metric you mean.")
        return

    # Rebind everything so generated components show real, in-scope numbers.
    recompute(session)
    session.reply('Done — ' + ', '.join(done) + '.')


generate_widget_state.set_body(generate_widget_body)
generate_widget_state.go_to(dashboard_state)


# --- 7. GUI Replies: a form built around what the user asked for -----------

_FIELDS_PROMPT = """The user wants to filter a sales dashboard. Decide which columns
the filter form should offer.

Available columns and what they hold:
{columns}

Respond with raw JSON only: {{"fields": ["<column>", ...]}}
Use exact column names from the list. Include only columns the user's request
implies; if the request is generic ("filter", "narrow it down"), return
["region", "channel", "category"]. At most 4 columns."""

_COLUMN_HELP = {
    'region': 'sales region (EMEA, APAC, ...)',
    'category': 'product category',
    'channel': 'Direct or Partner',
    'rep': 'sales representative',
    'date': 'order date — offers a date range picker',
    'revenue': 'order revenue in dollars — offers a minimum threshold',
    'units': 'units sold — offers a minimum threshold',
    'unit_price': 'price per unit — offers a minimum threshold',
    'discount': 'discount applied — offers a minimum threshold',
}


def choose_filter_fields(message: str) -> list[str]:
    """Ask the LLM which columns the user wants to filter on."""
    columns = '\n'.join(f'  {c} — {_COLUMN_HELP[c]}' for c in analytics.FILTERABLE)
    try:
        raw = gpt.predict(message, system_message=_FIELDS_PROMPT.format(columns=columns))
        fields = json.loads(_extract_json(raw)).get('fields') or []
    except Exception as exc:
        logger.warning(f'field selection failed: {exc}')
        fields = []
    picked = [f for f in fields if f in analytics.FILTERABLE][:4]
    return picked or ['region', 'channel', 'category']


def build_filter_form(session: Session, fields: list[str]) -> AgentGUI:
    """A self-contained filter form over *fields*, sent as a reply in the chat."""
    df = session.get('df')
    filters = filters_of(session)
    inputs = set()

    for order, field in enumerate(fields):
        kind = analytics.FILTERABLE[field]
        label = field.replace('_', ' ').title()

        if kind == 'categorical':
            inputs.add(InputField(
                name=field, description=label, component_id=field,
                field_type=InputFieldType.Dropdown, label=label,
                default_value=filters.values.get(field, 'All'), display_order=order,
                options=[SelectOption(label=v, value=v)
                         for v in ['All'] + analytics.options(df, field)],
            ))
        elif kind == 'date':
            first, last = analytics.date_range(df)
            inputs.add(InputField(
                name=field, description=label, component_id=field,
                field_type=InputFieldType.DateRange, label='Date range',
                help_text=f'Data runs {first} to {last}', display_order=order,
            ))
        else:
            low, high = analytics.numeric_range(df, field)
            inputs.add(InputField(
                name=field, description=label, component_id=field,
                field_type=InputFieldType.Slider, label=f'Minimum {label.lower()}',
                min_value=0, max_value=round(high), step=max(1, round(high / 50)),
                default_value=filters.minimums.get(field, 0), display_order=order,
            ))

    form = Form(
        name='filter_form', description='Refine the dashboard',
        title='Refine the dashboard', submit_label='Apply to dashboard',
        columns=1, display_order=0, inputFields=inputs,
    )
    screen = Screen(name='FilterForm', description='Filters', is_main_page=True,
                    view_elements={form})
    model = GUIModel(
        name='NovaFilterForm', package='com.besser.nova', versionCode='1',
        versionName='1.0', description='Filter form', modules={Module('nova', {screen})},
    )
    return AgentGUI(model, gui_id=FILTER_FORM_ID, persist=True, width='380px')


def offer_filter_body(session: Session):
    fields = choose_filter_fields(session.event.message)
    names = ', '.join(f.replace('_', ' ') for f in fields)
    session.reply(f'Sure — filter by {names}:')
    # GUI Reply: a rich, self-contained artifact *inside* the conversation, while the
    # dashboard keeps running in the full-page panel next to it.
    websocket_platform.reply_gui(session, build_filter_form(session, fields))


offer_filter_state.set_body(offer_filter_body)
offer_filter_state.go_to(dashboard_state)


def apply_filter_body(session: Session):
    # The framework persisted every field of the submitted form for us, and the form
    # was built at run time, so the agent reads back whatever fields it contained.
    values = session.gui_inputs.get(FILTER_FORM_ID, {})
    filters = filters_of(session)
    for field, value in values.items():
        if field in analytics.FILTERABLE:
            filters.set_field(field, value)

    stats = recompute(session)
    session.reply(f"Dashboard scoped to **{stats['scope']}** — "
                  f"${stats['revenue']:,.0f} across {stats['orders']} orders.")


apply_filter_state.set_body(apply_filter_body)
apply_filter_state.go_to(dashboard_state)


if __name__ == '__main__':
    agent.run()
