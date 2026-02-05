# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/besser-agentic-framework") # Replace with your directory path

import logging
import operator


import sys
sys.path.append("C:/Users/conrardy/Desktop/git/bot-framework") # Replace with your directory path

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

# Collect profile names from provided personalization mappings
profile_names = []
profile_names.append('Paraplegic')
profile_names.append('Elderly')
platform = agent.use_websocket_platform(use_ui=True, authenticate_users=True)
# LLM instantiation based on config['llm']
reply_llm = LLMOpenAI(
    agent=agent,
    name='gpt-5',
    parameters={}
)




ic_config = LLMIntentClassifierConfiguration(
    llm_name='gpt-5',
    parameters={},
    use_intent_descriptions=True,
    use_training_sentences=True,
    use_entity_descriptions=False,
    use_entity_synonyms=False
)

agent.set_default_ic_config(ic_config)


##############################
# INTENTS
##############################
Muscles_intent = agent.new_intent('Muscles_intent', [
    'I want muscles',
    ],
    description='Question about how to become muscular and which exercises to perform.'
)
Nutrition_intent = agent.new_intent('Nutrition_intent', [
    'Which food to eat?',
    ],
    description='Question about nutrition in gym.'
)
Other = agent.new_intent('Other', [
    ],
    description='Any question that does not fit in "Muscles" or "Nutrition"'
)

##############################
# PERSONALIZED INTENTS
##############################
# Intents for profile Paraplegic
Greeting_Paraplegic = agent.new_intent('Greeting_Paraplegic', [
    'Hi',
    'Hello',
    'Howdyyyy',
    ])
Good_Paraplegic = agent.new_intent('Good_Paraplegic', [
    'Good',
    'Fine',
    'I\\\'m alright',
    ])
Bad_Paraplegic = agent.new_intent('Bad_Paraplegic', [
    'Bad',
    'Not so good',
    'Could be better',
    ])
Muscles_Paraplegic = agent.new_intent('Muscles_Paraplegic', [
    'train',
    'muscles',
    'strong',
    ],
    description='Question about how to become buff'
)

# Intents for profile Elderly
Muscles_intent_Elderly = agent.new_intent('Muscles_intent_Elderly', [
    'Ech well Muskelen hunn',
    ],
    description='Question about how to become muscular and which exercises to perform.'
)
Nutrition_intent_Elderly = agent.new_intent('Nutrition_intent_Elderly', [
    'Wat fir Iessen soll ech iessen?',
    ],
    description='Question about nutrition in gym.'
)
Other_Elderly = agent.new_intent('Other_Elderly', [
    ],
    description='Any question that does not fit in "Muscles" or "Nutrition"'
)


##############################
# STATES
##############################

# Dummy entry state to fan out to profile-specific initial states
router_initial_state = agent.new_state('router_initial_state', initial=True)

Initial = agent.new_state('Initial')
Idle = agent.new_state('Idle')
TrainingPlan = agent.new_state('TrainingPlan')
Nutrition = agent.new_state('Nutrition')
OtherQuestions = agent.new_state('OtherQuestions')

##############################
# PROFILE STATES
##############################
# States for profile Paraplegic
initial_Paraplegic = agent.new_state('initial_Paraplegic')
greeting_Paraplegic = agent.new_state('greeting_Paraplegic')
bad_Paraplegic = agent.new_state('bad_Paraplegic')
good_Paraplegic = agent.new_state('good_Paraplegic')
TrainingPlan_Paraplegic = agent.new_state('TrainingPlan_Paraplegic')
# States for profile Elderly
Initial_Elderly = agent.new_state('Initial_Elderly')
Idle_Elderly = agent.new_state('Idle_Elderly')
TrainingPlan_Elderly = agent.new_state('TrainingPlan_Elderly')
Nutrition_Elderly = agent.new_state('Nutrition_Elderly')
OtherQuestions_Elderly = agent.new_state('OtherQuestions_Elderly')

##############################
# ROUTER TRANSITIONS TO PROFILE INITIAL STATES
##############################
router_initial_state.when_variable_matches_operation('user_profile', operator.eq, 'Paraplegic').go_to(initial_Paraplegic)
router_initial_state.when_variable_matches_operation('user_profile', operator.eq, 'Elderly').go_to(Initial_Elderly)


def router_body(session: Session):
    session.reply('I am routing you now')

router_initial_state.set_body(router_body)

# Initial
def Initial_body(session: Session):
    session.reply('Hi, I am your buddy, the fitness agent.')
Initial.set_body(Initial_body)
Initial.go_to(Idle)
# Idle
def Idle_body(session: Session):
    session.reply('I am here to answer any questions regarding exercises, nutrition and recovery.')
Idle.set_body(Idle_body)
Idle.when_intent_matched(Muscles_intent).go_to(TrainingPlan)
Idle.when_intent_matched(Other).go_to(OtherQuestions)
Idle.when_intent_matched(Nutrition_intent).go_to(Nutrition)
# TrainingPlan
def TrainingPlan_body(session: Session):
    session.reply('Focus on heavy compound lifts like squats, deadlifts, bench press, overhead press, and rows to build overall muscle mass. ')
    session.reply('Train 35 times per week, progressively increasing the weight while eating enough protein and calories to support growth. ')
    session.reply('Get good sleep and stay consistentmuscle comes from steady effort over time.')
TrainingPlan.set_body(TrainingPlan_body)
TrainingPlan.go_to(Idle)
# Nutrition
def Nutrition_body(session: Session):
    session.reply('Nutrition basics: Eat mostly whole foods (lean protein, vegetables, fruits, whole grains, healthy fats). Protein: ~1.62.2 g per kg of body weight daily..')
    session.reply('Match calories to your goal: slight surplus to gain muscle, deficit to lose fat, maintenance to stay the same. ')
    session.reply(' Carbs fuel training; fats support hormones.')
    session.reply(' Drink plenty of water and limit ultra-processed foods and alcohol. ')
    session.reply('Be consistent  results come from habits, not perfection')
Nutrition.set_body(Nutrition_body)
Nutrition.go_to(Idle)
# OtherQuestions
def OtherQuestions_body(session: Session):
    message = reply_llm.predict(session.event.message)
    session.reply(message)
OtherQuestions.set_body(OtherQuestions_body)
OtherQuestions.go_to(Idle)



##############################
# PROFILE STATE BODIES & TRANSITIONS
##############################
# initial (Paraplegic)
initial_Paraplegic.when_intent_matched(Greeting_Paraplegic).go_to(greeting_Paraplegic)
initial_Paraplegic.when_intent_matched(Muscles_Paraplegic).go_to(TrainingPlan_Paraplegic)
# greeting (Paraplegic)
def greeting_body_Paraplegic(session: Session):
    session.reply('How are you?')
greeting_Paraplegic.set_body(greeting_body_Paraplegic)
greeting_Paraplegic.when_intent_matched(Good_Paraplegic).go_to(good_Paraplegic)
greeting_Paraplegic.when_intent_matched(Bad_Paraplegic).go_to(bad_Paraplegic)
# bad (Paraplegic)
def bad_body_Paraplegic(session: Session):
    session.reply('I\\\\\'m sorry to hear that...')
bad_Paraplegic.set_body(bad_body_Paraplegic)
bad_Paraplegic.go_to(initial_Paraplegic)
# good (Paraplegic)
def good_body_Paraplegic(session: Session):
    session.reply('I am glad to hear that!')
good_Paraplegic.set_body(good_body_Paraplegic)
good_Paraplegic.go_to(initial_Paraplegic)
# TrainingPlan (Paraplegic)
def TrainingPlan_body_Paraplegic(session: Session):
    session.reply('Focus on heavy compound upper-body and seated lifts like bench press, incline press, seated overhead press with back support, seated rows or cable rows, and pull-ups or lat pulldowns to build overall muscle mass. Train 35 times per week, progressively increasing the weight or reps, using machines or cables when they provide safer support and stability. Eat enough protein and calories to support growth, get good sleep, and stay consistentmuscle comes from steady effort over time.')
TrainingPlan_Paraplegic.set_body(TrainingPlan_body_Paraplegic)
TrainingPlan_Paraplegic.go_to(initial_Paraplegic)

# Initial (Elderly)
def Initial_body_Elderly(session: Session):
    session.reply('Moien, ech sinn dain Fitness-Beroder.')
Initial_Elderly.set_body(Initial_body_Elderly)
Initial_Elderly.go_to(Idle_Elderly)
# Idle (Elderly)
def Idle_body_Elderly(session: Session):
    session.reply('Ech stinn zur Verfugung, fir all Froen iwwer Training, Ernarung an Erhuelung ze beantwerten.')
Idle_Elderly.set_body(Idle_body_Elderly)
Idle_Elderly.when_intent_matched(Muscles_intent_Elderly).go_to(TrainingPlan_Elderly)
Idle_Elderly.when_intent_matched(Other_Elderly).go_to(OtherQuestions_Elderly)
Idle_Elderly.when_intent_matched(Nutrition_intent_Elderly).go_to(Nutrition_Elderly)
# TrainingPlan (Elderly)
def TrainingPlan_body_Elderly(session: Session):
    session.reply('Konzentreier dech op schweier Grondubungen wei Kneibeugen, Kraizhiewen, de Bankdreck, den Iwwerkappdreck an Ruderen, fir allgemeng Muskelmass opzebauen.')
    session.reply('Traineier 35 mol d\\\'Woch, erheich d\\\'Gewiichter progressiv, a suerg fir genuch Protein a Kalorien, fir de Wuesstem z\\\'ennerstetzen.')
    session.reply('Prioriseier gudde Schlof a bleif konsequent; d\\\'Muskelen entweckele sech duerch bestannegen Asaz op Dauer.')
TrainingPlan_Elderly.set_body(TrainingPlan_body_Elderly)
TrainingPlan_Elderly.go_to(Idle_Elderly)
# Nutrition (Elderly)
def Nutrition_body_Elderly(session: Session):
    session.reply('Grondlage vun der Ernarung: Iess meeschtens onveraarbecht Liewensmettel (magere Proteinquellen, Gemeis, Uebst, Vollkarprodukter, gesond Fetter). Protein: ongefeier 1,62,2 g pro kg Kierpergewiicht pro Dag.')
    session.reply('Pass deng Kalorienopnam un dain Zil un: e klenge Iwwerschoss fir Muskelen opzebauen, e Defizit fir Fett ze verleieren oder Erhaltungsniveau, fir d\\\'selwecht ze bleiwen.')
    session.reply('Kuelenhydrater liwweren Energie fir den Training; Fetter aus der Ernarung ennerstetzen d\\\'hormonell Funktioun.')
    session.reply('Drenk vill Waasser a limiteier staark veraarbecht Liewensmettel an Alkohol.')
    session.reply('Bleif konsequent; Resultater entstinn aus Gewunnechten, net aus Perfektioun.')
Nutrition_Elderly.set_body(Nutrition_body_Elderly)
Nutrition_Elderly.go_to(Idle_Elderly)
# OtherQuestions (Elderly)
def OtherQuestions_body_Elderly(session: Session):
    message = reply_llm.predict(session.event.message)
    session.reply(message)
OtherQuestions_Elderly.set_body(OtherQuestions_body_Elderly)
OtherQuestions_Elderly.go_to(Idle_Elderly)


# RUN APPLICATION

if __name__ == '__main__':
    agent.run()