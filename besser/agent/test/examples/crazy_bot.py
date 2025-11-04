# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/besser-agentic-framework") # Replace with your directory path

import logging
import operator


import json as json
import sys
sys.path.append("C:/Users/conrardy/Desktop/git/bot-framework") # Replace with your directory pat


from besser.agent.core.agent import Agent
from besser.agent.nlp.llm.llm_huggingface import LLMHuggingFace
from besser.agent.nlp.llm.llm_huggingface_api import LLMHuggingFaceAPI
from besser.agent.nlp.llm.llm_openai_api import LLMOpenAI
from besser.agent.nlp.llm.llm_replicate_api import LLMReplicate
from besser.agent.core.session import Session
from besser.agent.nlp.intent_classifier.intent_classifier_configuration import LLMIntentClassifierConfiguration, SimpleIntentClassifierConfiguration
from besser.agent.nlp.speech2text.openai_speech2text import OpenAISpeech2Text
from besser.agent.nlp.text2speech.openai_text2speech import OpenAIText2Speech

# Configure the logging module
logging.basicConfig(level=logging.INFO, format='{levelname} - {asctime}: {message}', style='{')


# Create the bot
agent = Agent('Agent_Diagram')
# Load bot properties stored in a dedicated file
agent.load_properties('config.ini')

# Define the platform your chatbot will use

stt = OpenAISpeech2Text(agent=agent, model_name="whisper-1")
tts = OpenAIText2Speech(agent=agent, model_name="gpt-4o-mini-tts")
personalized_messages = json.loads(r'''{
  "Hi! How are you?": {
    "[\"formal\", \"simple\"]": "Hello. How are you?",
    "[\"french\", \"formal\", \"simple\"]": "Bonjour. Comment allez-vous ?",
    "[\"french\", \"formal\"]": "Bonjour. Comment allez-vous ?",
    "[\"french\", \"simple\"]": "Salut ! Comment \u00e7a va ?",
    "[\"luxembourgish\", \"formal\", \"simple\"]": "Moien. W\u00e9i geet et dir?",
    "[\"luxembourgish\", \"formal\"]": "Moien. W\u00e9i geet et dir?",
    "[\"luxembourgish\", \"simple\"]": "Moien! W\u00e9i geet et dir?",
    "formal": "Hello. How are you?",
    "french": "Salut ! Comment \u00e7a va ?",
    "luxembourgish": "Moien! W\u00e9i geet et dir?",
    "simple": "Hi! How are you?"
  },
  "I am glad to hear that!": {
    "[\"formal\", \"simple\"]": "I am pleased to hear that.",
    "[\"french\", \"formal\", \"simple\"]": "Je suis heureux de l\u2019apprendre.",
    "[\"french\", \"formal\"]": "Je me r\u00e9jouis de l\u2019apprendre.",
    "[\"french\", \"simple\"]": "Je suis heureux de l\u2019apprendre !",
    "[\"luxembourgish\", \"formal\", \"simple\"]": "Ech sinn frou, dat ze h\u00e9ieren.",
    "[\"luxembourgish\", \"formal\"]": "Ech sinn frou, dat ze h\u00e9ieren.",
    "[\"luxembourgish\", \"simple\"]": "Ech free\u00eb mech, dat ze h\u00e9ieren!",
    "formal": "I am pleased to hear that.",
    "french": "Je suis heureux de l\u2019apprendre !",
    "luxembourgish": "Ech free\u00eb mech, dat ze h\u00e9ieren!",
    "simple": "I am glad to hear that!"
  },
  "I am the entity designated as the Greeting Bot, an artificially instantiated construct whose primary operational purpose is to serve as an experimental exemplar within the procedural ecosystem of the Besser Agentic Framework. My existence is dedicated to facilitating interactive engagement, thereby enabling human participants to evaluate and empirically validate the behavioral parameters of autonomous digital agents generated through said framework.": {
    "[\"formal\", \"simple\"]": "I am the Greeting Bot. I am an artificial agent made to test the Besser Agentic Framework. I talk with people so they can check and confirm how agents from this framework behave.",
    "[\"french\", \"formal\", \"simple\"]": "Je m\u2019appelle \u00ab Greeting Bot \u00bb. Je suis un agent artificiel cr\u00e9\u00e9 comme exemple de test pour le Besser Agentic Framework. Mon r\u00f4le est de faciliter les \u00e9changes. Cela permet aux personnes de tester et de v\u00e9rifier le comportement des agents autonomes cr\u00e9\u00e9s par ce framework.",
    "[\"french\", \"formal\"]": "Je suis d\u00e9sign\u00e9 en tant que Greeting Bot, une entit\u00e9 artificiellement instanci\u00e9e dont la finalit\u00e9 principale est de servir d\u2019exemple exp\u00e9rimental au sein de l\u2019\u00e9cosyst\u00e8me proc\u00e9dural du Besser Agentic Framework. Mon r\u00f4le est de faciliter l\u2019engagement interactif, permettant ainsi aux participants humains d\u2019\u00e9valuer et de valider empiriquement les param\u00e8tres comportementaux des agents num\u00e9riques autonomes g\u00e9n\u00e9r\u00e9s par ledit cadre.",
    "[\"french\", \"simple\"]": "Je m\u0027appelle Greeting Bot. Je suis un robot de test pour le Besser Agentic Framework. Mon r\u00f4le est de faciliter les conversations, afin que les personnes puissent tester et v\u00e9rifier comment se comportent les programmes autonomes cr\u00e9\u00e9s par ce syst\u00e8me.",
    "[\"luxembourgish\", \"formal\", \"simple\"]": "Ech sinn e Begr\u00e9issungsbot. Ech sinn hei als Beispill am Besser Agentic Framework. Meng Aufgab ass et, d\u0027Leit beim Matmaache ze h\u00ebllefen, sou datt si d\u0027Verhalen vun de digitale Agenten aus d\u00ebsem Framework teste a kontroll\u00e9ieren.",
    "[\"luxembourgish\", \"formal\"]": "Ech sinn als \"Greeting Bot\" bezeechent, eng k\u00ebnschtlech erschaf Entit\u00e9it, d\u00e9i haapts\u00e4chlech dozou d\u00e9ngt, als experimentellt Exemplar am prozeduralen \u00d6kosystem vum Besser Agentic Framework ze d\u00e9ngen. Meng Roll ass et, den interaktiven Austausch ze erliichteren, sou datt m\u00ebnschlech Participanten d\\\u0027Verhalensparameter vun autonome digitale Agenten, d\u00e9i duerch dat genannte Framework gener\u00e9iert ginn, evalu\u00e9ieren an empir\u00ebsch valid\u00e9ieren k\u00ebnnen.",
    "[\"luxembourgish\", \"simple\"]": "Ech sinn de \"Greeting Bot\". Ech sinn en k\u00ebnschtleche Bot. Meng Haaptaufgab ass, am \"Besser Agentic Framework\" als Test-Bot ze d\u00e9ngen. Ech maachen d\u0027Gespr\u00e9icher m\u00e9i einfach, sou datt d\u0027Leit d\u0027Verhale vun de digitale Agenten k\u00ebnne testen an iwwerpr\u00e9iwen.",
    "formal": "I am designated the Greeting Bot, an artificially instantiated entity whose primary purpose is to serve as an experimental exemplar within the procedural ecosystem of the Besser Agentic Framework. My role is to facilitate interactive engagement, thereby enabling human participants to evaluate and empirically validate the behavioral parameters of autonomous digital agents generated through said framework.",
    "french": "Je suis l\u2019entit\u00e9 d\u00e9sign\u00e9e sous le nom de Greeting Bot, un construit instanci\u00e9 artificiellement dont la finalit\u00e9 op\u00e9rationnelle principale est de servir d\u2019exemple exp\u00e9rimental au sein de l\u2019\u00e9cosyst\u00e8me proc\u00e9dural du Besser Agentic Framework. Mon existence est d\u00e9di\u00e9e \u00e0 faciliter les interactions, permettant ainsi aux participants humains d\u2019\u00e9valuer et de valider empiriquement les param\u00e8tres comportementaux des agents num\u00e9riques autonomes g\u00e9n\u00e9r\u00e9s par ledit Besser Agentic Framework.",
    "luxembourgish": "Ech sinn d\u00e9i Entit\u00e9it, d\u00e9i als \"Greeting Bot\" bezeechent g\u00ebtt, e k\u00ebnschtlech instanti\u00e9iert Konstrukt mat dem prim\u00e4ren operationelle Zweck, als experimentellt Exemplar am prozedurale \u00d6kosystem vum \"Besser Agentic Framework\" ze d\u00e9ngen. Meng Existenz ass der Erliichterung vun interaktivem Austausch gewidmet, fir domat m\u00ebnschleche Participanten ze erm\u00e9iglechen, d\u0027Verhalensparameter vun autonom digitalen Agenten, d\u00e9i duerch dat genannt Framework gener\u00e9iert goufen, ze evalu\u00e9ieren an empir\u00ebsch ze valid\u00e9ieren.",
    "simple": "I am the Greeting Bot. I am a test bot for a system called the Besser Agentic Framework. My job is to talk with people. This helps them test how the agents it makes behave."
  },
  "I\\\u0027m sorry to hear that...": {
    "[\"formal\", \"simple\"]": "I am sorry to hear that.",
    "[\"french\", \"formal\", \"simple\"]": "Je suis d\u00e9sol\u00e9 de l\u2019apprendre.",
    "[\"french\", \"formal\"]": "Je regrette de l\u2019apprendre.",
    "[\"french\", \"simple\"]": "Je suis d\u00e9sol\u00e9 de l\u2019apprendre...",
    "[\"luxembourgish\", \"formal\", \"simple\"]": "Et deet mir Leed, dat ze h\u00e9ieren.",
    "[\"luxembourgish\", \"formal\"]": "Et deet mir Leed, dat ze h\u00e9ieren.",
    "[\"luxembourgish\", \"simple\"]": "Dat deet mir Leed...",
    "formal": "I am sorry to hear that.",
    "french": "Je suis d\u00e9sol\u00e9 de l\u2019apprendre...",
    "luxembourgish": "Dat deet mir Leed...",
    "simple": "I\u0027m sorry to hear that..."
  }
}''')

# load the personalization rules from the generator context into a Python variable called `rules`
rules = json.loads(r'''[
  {
    "feature": "gender",
    "rules": []
  },
  {
    "feature": "address",
    "rules": []
  },
  {
    "feature": "lastName",
    "rules": []
  },
  {
    "feature": "age",
    "rules": [
      {
        "feature": "age",
        "id": "1760685892307-r8a8ue",
        "operator": "\u003e=",
        "target": "agentStyle",
        "targetValue": "formal",
        "value": 30
      },
      {
        "feature": "age",
        "id": "1761046219218-23zq5t",
        "operator": "\u003c",
        "target": "agentLanguageComplexity",
        "targetValue": "simple",
        "value": 10
      }
    ]
  },
  {
    "feature": "nationality_iso3166",
    "rules": [
      {
        "feature": "nationality_iso3166",
        "id": "1760685919268-8zjs5h",
        "operator": "is",
        "target": "agentLanguage",
        "targetValue": "french",
        "value": "French"
      },
      {
        "feature": "nationality_iso3166",
        "id": "1761055611006-vz73la",
        "operator": "is",
        "target": "agentLanguage",
        "targetValue": "luxembourgish",
        "value": "Lux"
      }
    ]
  },
  {
    "feature": "firstName",
    "rules": []
  }
]''')




def evaluate_rules(session: Session):
    """Evaluate rules and return a dict of applied targets -> values.

    rules_list: list of feature-rule dicts like the `rules` variable.
    user: dict of user features.
    Returns: dict mapping target names (e.g. 'agentStyle') -> targetValue (e.g. 'informal')
    """

    rules_list = rules
    applied = {}
    for feature_block in rules_list:
        feature = feature_block.get('feature')
        for r in feature_block.get('rules', []):
            # If the user doesn't have this feature, skip
            if session.get(feature) is None:
                continue
            user_val = session.get(feature)
            op = r.get('operator')
            rule_val = r.get('value')

            matched = False
            try:
                # numeric comparisons if possible
                if op in {'<', '<=', '>', '>=', '==', '!='}:
                    uv = float(user_val)
                    rv = float(rule_val)
                    if op == '<':
                        matched = uv < rv
                    elif op == '<=':
                        matched = uv <= rv
                    elif op == '>':
                        matched = uv > rv
                    elif op == '>=':
                        matched = uv >= rv
                    elif op == '==':
                        matched = uv == rv
                    elif op == '!=':
                        matched = uv != rv
                elif op == 'is':
                    # string equality, case-insensitive
                    matched = str(user_val).lower() == str(rule_val).lower()
                else:
                    # unknown operator: try python eval-style fallback for safety
                    matched = False
            except Exception:
                # If conversion failed, try string comparison for equality-like ops
                if op == 'is':
                    matched = str(user_val).lower() == str(rule_val).lower()
                else:
                    matched = False

            if matched:
                applied[r.get('target')] = r.get('targetValue')

    return applied


def select_variant_for_message(variants_mapping, applied_targets):
    """Select the best variant from variants_mapping given applied target values.

    variants_mapping: dict where keys are variant selectors (e.g. 'formal', 'french', '["french","informal"]')
    applied_targets: dict mapping target names -> values (e.g. {'agentStyle':'informal','agentLanguage':'french'})

    Selection strategy:
      1) Prefer a JSON-list key whose elements (as a set) equal the set of applied target values.
      2) Otherwise prefer a single-key match where the key equals one of the applied values.
      3) Otherwise fallback to a 'formal' key if present, then any available variant, else None.
    """
    values = list(applied_targets.values()) if applied_targets else []
    values_set = set(values)

    best_key = None
    best_score = 0

    for k, v in variants_mapping.items():
        score = 0
        # try list-like keys first
        if isinstance(k, str) and k.startswith('[') and k.endswith(']'):
            try:
                parsed = json.loads(k)
                if isinstance(parsed, list):
                    parsed_set = set(parsed)
                    # exact list match (all applied values match the list)
                    if parsed_set == values_set and len(parsed) == len(values):
                        score = 1000 + len(parsed)
                    else:
                        # partial overlap counts lightly
                        score = len(parsed_set & values_set)
            except Exception:
                score = 0
        else:
            # simple key match gets higher priority than partial list overlaps
            if k in values_set:
                score = 500

        if score > best_score:
            best_score = score
            best_key = k

    if best_key is not None:
        return variants_mapping[best_key]

    print("No suitable variant found.")
    print(variants_mapping)
    # any variant


    return None



def choose_variant_for_message(base_msg, session: Session, applied=None):
    """Choose a single best variant for `base_msg` given `user` and `rules_list`.

    If `applied` (dict of applied targets) is provided it will be reused; otherwise
    the function will evaluate the rules for the user.
    Returns the selected message string (or the base message if no variant found).
    """

    if applied is None:
        applied = evaluate_rules(session)
    print("Applied rules:", applied)
    print("message", base_msg)
    variants = personalized_messages.get(base_msg)
    if not variants or len(applied) == 0:
        return base_msg
    choice = select_variant_for_message(variants, applied)
    print("Chosen variant:", choice)
    return choice if choice is not None else base_msg
 





platform = agent.use_websocket_platform(use_ui=True, persist_users=True)


# LLM instantiation based on config['llm']

##############################
# INTENTS
##############################

Greeting = agent.new_intent('Greeting', [
    'Hi',
    'Hello',
    'Howdy',
    ])

Good = agent.new_intent('Good', [
    'Good',
    'Fine',
    'I\\\'m alright',
    ])

Bad = agent.new_intent('Bad', [
    'Bad',
    'Not so good',
    'Could be better',
    ])

##############################
# STATES
##############################

initial = agent.new_state('initial', initial=True)
greeting = agent.new_state('greeting')
bad = agent.new_state('bad')
good = agent.new_state('good')


# initial

def initial_body(session: Session):
    
    session.reply(choose_variant_for_message('I am the entity designated as the Greeting Bot, an artificially instantiated construct whose primary operational purpose is to serve as an experimental exemplar within the procedural ecosystem of the Besser Agentic Framework. My existence is dedicated to facilitating interactive engagement, thereby enabling human participants to evaluate and empirically validate the behavioral parameters of autonomous digital agents generated through said framework.', session))
    platform.reply_speech("I am the entity designated as the Greeting Bot, an artificially instantiated construct whose primary operational purpose is to serve as an experimental exemplar within the procedural ecosystem of the Besser Agentic Framework.", session)
    
    

initial.set_body(initial_body)


initial.when_intent_matched(Greeting).go_to(initial)

# greeting

def greeting_body(session: Session):
    
    session.reply(choose_variant_for_message('Hi! How are you?', session))
    
    
    

greeting.set_body(greeting_body)


greeting.when_intent_matched(Good).go_to(good)
greeting.when_intent_matched(Bad).go_to(bad)

# bad

def bad_body(session: Session):
    
    session.reply(choose_variant_for_message('I\'m sorry to hear that...', session))
    
    
    

bad.set_body(bad_body)



bad.go_to(initial)

# good

def good_body(session: Session):
    
    session.reply(choose_variant_for_message('I am glad to hear that!', session))
    
    
    

good.set_body(good_body)



good.go_to(initial)

# RUN APPLICATION

if __name__ == '__main__':
    agent.run()