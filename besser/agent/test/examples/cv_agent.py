from besser.agent.core.requirement.complex_requirement import AND, OR, NOT
from besser.agent.core.requirement.concrete_requirement import ConcreteRequirement
from besser.agent.core.requirement.abstract_requirement import AbstractRequirement


import logging

from besser.agent.core.agent import Agent
from besser.agent.core.session import Session
from besser.agent.cv.object_detection.yoloworld_object_detector import YOLOWorldObjectDetector
from besser.agent.cv.vllm.vllm_openai_api import VLLMOpenAI

# Configure the logging module
logging.basicConfig(level=logging.INFO, format='{levelname} - {asctime}: {message}', style='{')

# Create the agent
agent = Agent('greetings_agent')
# Load agent properties stored in a dedicated file
agent.load_properties('config.ini')
# Define the platform your agent will use
websocket_platform = agent.use_websocket_platform(use_ui=True, video_input=True)

# Image entities

person = agent.new_concrete_entity('person')
phone = agent.new_concrete_entity('phone')
bottle = agent.new_concrete_entity('bottle')
# TODO: NON-BOOLEAN PROPERTIES? e.g. phone_brand (values: iphone, samsung)
indoors = agent.new_abstract_entity(name='indoors', attributes={'description': 'The picture is taken in an indoor environment (i.e., not outdoors)'})
iphone = agent.new_abstract_entity(name='iphone', attributes={'description': 'The phone in the image (if there is one) is an iPhone (Apple)'})

yolo_model = YOLOWorldObjectDetector(agent=agent, name='yolov8l-worldv2', model_path='yolo_weights/yolov8l-worldv2.pt', parameters={
    'classes': [image_entity.name for image_entity in agent.concrete_entities]
})
vllm = VLLMOpenAI(agent, 'gpt-4o', {})

requirement = agent.new_requirement('scenario1')
requirement.set(
    AND([
        AbstractRequirement(name='iphone', abstract_entity=iphone, attributes={'confidence': 0.5}),
        ConcreteRequirement(name='person', concrete_entity=person, attributes={'max': 3, 'confidence': 0.3}),  # choose which model to use at property level or requirement level
        ConcreteRequirement(name='phone', concrete_entity=phone, attributes={'confidence': 0.5})
    ])
)
initial_state = agent.new_state('initial_state', initial=True)
person_state = agent.new_state('person_state')


initial_state.when_requirement_matched_go_to(requirement, person_state)


def hello_body(session: Session):
    session.reply('Hi!')


def person_body(session: Session):
    session.reply('I can see you!')


person_state.set_body(person_body)
person_state.when_no_intent_matched_go_to(initial_state)

# RUN APPLICATION

if __name__ == '__main__':
    agent.run()
