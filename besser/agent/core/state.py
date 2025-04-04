import inspect
import traceback
from collections import deque
from typing import Any, Callable, TYPE_CHECKING, Union

from besser.agent.core.transition.event import Event
from besser.agent.core.transition.transition import Transition
from besser.agent.core.transition.transition_builder import TransitionBuilder
from besser.agent.library.intent.intent_library import fallback_intent
from besser.agent.library.transition.event import ReceiveTextEvent, ReceiveFileEvent
from besser.agent.library.transition.condition import IntentMatcher, VariableOperationMatcher
from besser.agent.core.transition.condition import Condition
from besser.agent.core.intent.intent import Intent
from besser.agent.core.session import Session
from besser.agent.exceptions.exceptions import BodySignatureError, ConflictingAutoTransitionError, \
    DuplicatedIntentMatchingTransitionError, IntentNotFound
from besser.agent.exceptions.logger import logger
from besser.agent.library.transition.condition_functions import file_type
from besser.agent.library.state.state_library import default_body, default_fallback_body
from besser.agent.nlp.intent_classifier.intent_classifier_configuration import IntentClassifierConfiguration, \
    SimpleIntentClassifierConfiguration

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent


class State:
    """The State core component of an agent.

    The agent relies on a state machine to define its execution logic. Each state can run a set of actions, and the agent
    can navigate to other states through transitions that are triggered when events occur (e.g. an intent is matched).

    Args:
        agent (Agent): the agent the state belongs to
        name (str): the state's name
        initial (bool): whether the state is initial or not
        ic_config (IntentClassifierConfiguration): the intent classifier configuration of the state

    Attributes:
        _agent (Agent): The agent the state belongs to
        _name (str): The state name
        _initial (bool): Whether the state is initial or not
        _body (Callable[[Session], None]): The state body. It is a callable that takes as argument a
            :class:`~besser.agent.core.session.Session`. It will be run whenever the agent moves to this state.
        _fallback_body (Callable[[Session], None]): The state fallback body. It is a callable that takes as argument a
            :class:`~besser.agent.core.session.Session`. It will be run whenever the agent tries to move to another state,
            but it can't (e.g. an intent is matched but none of the current state's transitions are triggered on that
            intent)
        _ic_config (IntentClassifierConfiguration): the intent classifier configuration of the state
        _transition_counter (int): Count the number of transitions of this state. Used to name the transitions.
        intents (list[Intent]): The state intents, i.e. those that can be matched from a specific state
        transitions (list[Transition]): The state's transitions to other states
    """

    def __init__(
            self,
            agent: 'Agent',
            name: str,
            initial: bool = False,
            ic_config: IntentClassifierConfiguration or None = None
    ):
        self._agent: 'Agent' = agent
        self._name: str = name
        self._initial: bool = initial
        self._body: Callable[[Session], None] = default_body
        self._fallback_body: Callable[[Session], None] = default_fallback_body
        if not ic_config:
            ic_config = SimpleIntentClassifierConfiguration()
        self._ic_config: IntentClassifierConfiguration = ic_config
        self._transition_counter: int = 0
        self.intents: list[Intent] = []
        self.transitions: list[Transition] = []

    @property
    def agent(self):
        """Agent: The state's agent."""
        return self._agent

    @property
    def name(self):
        """str: The state name"""
        return self._name

    @property
    def initial(self):
        """bool: The initial status of the state (initial or non-initial)."""
        return self._initial

    @property
    def ic_config(self):
        """IntentClassifierConfiguration: the intent classifier configuration of the state."""
        return self._ic_config

    def __eq__(self, other):
        if type(other) is type(self):
            return self._name == other.name and self._agent.name == other.agent.name
        else:
            return False

    def __hash__(self):
        return hash((self._name, self._agent.name))

    def _t_name(self):
        """Name generator for transitions. Transition names are generic and enumerated. On each call, a new name is
        generated and the transition counter is incremented for the next name.

        Returns:
            str: a name for the next transition
        """
        self._transition_counter += 1
        return f"t_{self._transition_counter}"

    def set_global(self, intent: Intent):
        """Set state as globally accessible state.

        Args:
            intent (Intent): the intent that should trigger the jump to the global state
        """
        self.agent.global_initial_states.append((self, intent))
        self.agent.global_state_component[self] = [self]
        # Check whether the states from the global component are already in the list
        # Currently only works for linear states
        transitions = self.transitions
        while transitions:
            transition = transitions[0]
            if transition not in self.agent.global_state_component[self]:
                self.agent.global_state_component[self].append(transition.dest)
            transitions = transition.dest.transitions

    def set_body(self, body: Callable[[Session], None]) -> None:
        """Set the state body.

        Args:
            body (Callable[[Session], None]): the body
        """
        body_signature = inspect.signature(body)
        body_template_signature = inspect.signature(default_body)
        if body_signature.parameters != body_template_signature.parameters:
            raise BodySignatureError(self._agent, self, body, body_template_signature, body_signature)
        self._body = body

    def set_fallback_body(self, body: Callable[[Session], None]):
        """Set the state fallback body.

        Args:
            body (Callable[[Session], None]): the fallback body
        """
        body_signature = inspect.signature(body)
        body_template_signature = inspect.signature(default_fallback_body)
        if body_signature.parameters != body_template_signature.parameters:
            raise BodySignatureError(self._agent, self, body, body_template_signature, body_signature)
        self._fallback_body = body

    def _check_global_state(self, dest: 'State'):
        """Add state to global state component if condition is met.

        If the previous state is a global state, add this state to the component's list
        of the global state.

        Args:
            dest (State): the destination state
        """
        if any(self in global_state for global_state in self.agent.global_initial_states):
            self.agent.global_state_component[self].append(dest)
            return
        for global_state in self.agent.global_state_component:
            if self in self.agent.global_state_component[global_state]:
                self.agent.global_state_component[global_state].append(dest)

    def when_event(self, event: Event) -> TransitionBuilder:
        for transition in self.transitions:
            if transition.is_auto():
                raise ConflictingAutoTransitionError(self._agent, self)
        return TransitionBuilder(source=self, event=event)

    def when_condition(
            self,
            function: Union[
                Callable[[Session], bool],
                Callable[[Session, dict], bool]
            ],
            params: dict = None
    ) -> TransitionBuilder:
        for transition in self.transitions:
            if transition.is_auto():
                raise ConflictingAutoTransitionError(self._agent, self)
        transition_builder = TransitionBuilder(source=self, event=None)
        return transition_builder.with_condition(function, params)

    def when_intent_matched(self, intent: Intent) -> TransitionBuilder:
        if intent in self.intents:
            raise DuplicatedIntentMatchingTransitionError(self, intent)
        if intent not in self._agent.intents:
            raise IntentNotFound(self._agent, intent)
        for transition in self.transitions:
            if transition.is_auto():
                raise ConflictingAutoTransitionError(self._agent, self)
        self.intents.append(intent)
        event: ReceiveTextEvent = ReceiveTextEvent()
        condition: Condition = IntentMatcher(intent)
        transition_builder: TransitionBuilder = TransitionBuilder(source=self, event=event, condition=condition)
        return transition_builder

    def go_to(self, dest: 'State') -> None:
        """Create a new `auto` transition on this state.

        This transition needs no event to be triggered, which means that when the agent moves to a state
        that has an `auto` transition, the agent will move to the transition's destination state
        unconditionally without waiting for user input. This transition cannot be combined with other
        transitions.

        Args:
            dest (State): the destination state
        """

        if self.transitions:
            raise ConflictingAutoTransitionError(self._agent, self)
        transition_builder: TransitionBuilder = TransitionBuilder(source=self, event=None, condition=None)
        transition_builder.go_to(dest)

    def when_no_intent_matched(self) -> TransitionBuilder:
        for transition in self.transitions:
            if transition.is_auto():
                raise ConflictingAutoTransitionError(self._agent, self)
        event: ReceiveTextEvent = ReceiveTextEvent()
        condition: Condition = IntentMatcher(fallback_intent)
        transition_builder: TransitionBuilder = TransitionBuilder(source=self, event=event, condition=condition)
        return transition_builder

    def when_variable_matches_operation(
            self,
            var_name: str,
            operation: Callable[[Any, Any], bool],
            target: Any,
    ) -> TransitionBuilder:
        for transition in self.transitions:
            if transition.is_auto():
                raise ConflictingAutoTransitionError(self._agent, self)
        condition: Condition = VariableOperationMatcher(var_name, operation, target)
        transition_builder: TransitionBuilder = TransitionBuilder(source=self, condition=condition)
        return transition_builder

    def when_file_received(self, allowed_types: list[str] or str = None) -> TransitionBuilder:
        for transition in self.transitions:
            if transition.is_auto():
                raise ConflictingAutoTransitionError(self._agent, self)
        event = ReceiveFileEvent()
        transition_builder: TransitionBuilder = TransitionBuilder(source=self, event=event)
        transition_builder.with_condition(function=file_type, params={'allowed_types': allowed_types})
        return transition_builder

    def check_transitions(self, session: Session):
        """Check the transition and triggers the one that match

        When checking transition, the priority is based on transition order.
        For a given transition expecting an event to happen, the first event matching will be used.
        If a user message event is received but does not match the transition, run the fallback body

        Args:
            session (Session): the current session
        """
        run_fallback = False
        for i, next_transition in enumerate(self.transitions):
            if next_transition.is_event():
                # TODO: Decide policy to remove events
                fallback_deque = deque()
                while session.events:
                    session.event = session.events.pop()
                    if isinstance(session.event, ReceiveTextEvent):
                        session.event.predict_intent(session)
                    if next_transition.evaluate(session, session.event):
                        session.move(next_transition)
                        # TODO: Make this configurable (we can consider remove all the previously checked events)
                        session.events.extend(fallback_deque)  # We restore the queue but with the matched event removed
                        return
                    if isinstance(session.event, ReceiveTextEvent) and session.event.human:
                        # There is a ReceiveTextEvent and we couldn't match any transition so far
                        run_fallback = True
                        if i < len(self.transitions)-1:
                            # We only append ReceiveTextEvent (human) if we didn't finish checking all transitions
                            fallback_deque.appendleft(session.event)
                    else:
                        fallback_deque.appendleft(session.event)
                session.events.extend(fallback_deque)
            else:
                if next_transition.is_condition_true(session):
                    session.move(next_transition)
                    return
        if run_fallback:
            # There was one or more transitions with ReceiveMessageEvent and one ReceiveMessageEvent (human)
            # that didn't match any transition
            logger.info(f"[{self._name}] Running fallback body {self._fallback_body.__name__}")
            try:
               self._fallback_body(session)
            except Exception as _:
               logger.error(f"An error occurred while executing '{self._fallback_body.__name__}' of state"
                             f"'{self._name}' in agent '{self._agent.name}'. See the attached exception:")
        session.event = None

    def run(self, session: Session) -> None:
        """Run the state (i.e. its body). After running the body, check if the first defined transition of the state is
        an `auto` transition, and if so, move to its destination state.

        Args:
            session (Session): the user session
        """
        logger.info(f"[{self._name}] Running body {self._body.__name__}")
        try:
            self._body(session)
        except Exception as _:
            logger.error(f"An error occurred while executing '{self._body.__name__}' of state '{self._name}' in agent '"
                          f"{self._agent.name}'. See the attached exception:")
            traceback.print_exc()
        # Reset current event
        session.event = None
