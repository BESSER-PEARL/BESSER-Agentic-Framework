from baf.core.processors.processor import Processor
from baf.nlp.llm.llm import LLM
from baf.core.agent import Agent
from baf.core.session import Session
from baf.nlp.nlp_engine import NLPEngine


class UserAdaptationProcessor(Processor):
    """The UserAdaptationProcessor takes into account the user's profile and adapts the agent's responses to fit the
    profile. The goal is to increase the user experience.

    This processor uses an LLM prediction for each processed message, with the current profile for the session.
    Set the profile with :meth:`add_user_model` before processing the session's first outgoing message.

    Args:
        agent (Agent): The agent the processor belongs to
        llm_name (str): the name of the LLM to use.
        context (str): additional context to improve the adaptation. Should include information about the agent itself
            and the task it should accomplish

    Attributes:
        agent (Agent): The agent the processor belongs to
        _llm_name (str): the name of the LLM to use.
        _context (str): additional context to improve the adaptation. should include information about the agent itself
        and the task it should accomplish
        _user_model (dict): dictionary containing the user models
    """
    def __init__(self, agent: 'Agent', llm_name: str, context: str = None):
        super().__init__(agent=agent, agent_messages=True)
        self._llm_name: str = llm_name
        self._nlp_engine: 'NLPEngine' = agent.nlp_engine
        self._user_model: dict = {}
        if context:
            self._context = context
        else:
            self._context = "You are an agent."

    # TODO: add capability to improve/change prompt of context
    def process(self, session: 'Session', message: str) -> str:
        """Method to process a message and adapt its content based on a given user model.

        The stored user model will be fetched and sent as part of the context.

        Args:
            session (Session): the current session
            message (str): the message to be processed

        Returns:
            str: the processed message
        """
        llm: LLM = self._nlp_engine._llms[self._llm_name]
        user_context = f"{self._context}\n\
                You are capable of adapting your predefined answers based on a given user profile.\
                Your goal is to increase the user experience by adapting the messages based on the different attributes of the user\
                profile as best as possible and take all the attributes into account.\
                You are free to adapt the messages in any way you like.\
                The user should relate more. This is the user's profile\n \
                {str(self._user_model[session.id])}"
        prompt = f"You need to adapt this message: {message}\n Only respond with the adapted message!"
        llm_response: str = llm.predict(prompt, session=session, system_message=user_context)
        return llm_response

    def add_user_model(self, session: 'Session', user_model: dict) -> None:
        """Store or replace the profile used for this session's subsequent messages.

        Profiles are kept in memory, indexed by session id. Calling this method again replaces the whole profile
        for that session without changing other sessions' profiles.

        Args:
            session (Session): the current session
            user_model (dict): the user model of a given user
        """
        self._user_model[session.id] = user_model
