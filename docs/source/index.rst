BESSER Agentic Framework
========================

.. toctree::
   :maxdepth: 1
   :hidden:

   your_first_agent
   your_first_multiagent
   wiki
   examples
   release_notes
   api


The `BESSER Agentic Framework (BAF) <https://github.com/BESSER-PEARL/BESSER-Agentic-Framework>`_ is part of the BESSER
(Building Better Smart Software Faster) project at the Luxembourg Institute of Science and Technology (LIST).
It aims to make the design and implementation of agents easier and accessible for everyone.

Quickstart
----------

Requirements
~~~~~~~~~~~~

- Python 3.11
- Recommended: Create a virtual environment
  (e.g. `venv <https://docs.python.org/3/library/venv.html>`_,
  `conda <https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_)
- Install the `package <https://pypi.org/project/besser-agentic-framework/>`_:

.. code:: bash

    pip install besser-agentic-framework

This command will install the base package with the core dependencies, but will omit some optional dependencies.

You can add the following tags to the installation:

- ``extras``: It will install the necessary dependencies for some additional agent functionalities (e.g., RAG, Speech-to-Text, plotly, opencv).
- ``llms``: Necessary dependencies to run LLMs (openai, replicate, transformers)
- ``torch``: To install PyTorch, necessary for the Simple Intent Classifier (PyTorch implementation) and HuggingFace models
- ``tensorflow``: Necessary for the Simple Intent Classifier (Tensorflow implementation) and some HuggingFace models. Since tensorflow is a very heavy package, this allows to install it only if necessary
- ``docs``: Dependencies to compile the project documentation (the one you are reading now)
- ``all``: **It installs all the dependencies at once**

This is how you would install the package with additional dependencies:

.. code:: bash

    pip install besser-agentic-framework[extras,llms,tensorflow]

If you cloned the repository, you can install the dependencies in 2 ways:

.. code:: bash

    pip install -e .[extras]

or by referencing to the requirements files:

.. code:: bash

    pip install -r requirements/requirements-extras.txt

Note that if you want to set your agent's language to Luxembourgish and are using the package installed with pip, you will need to manually install the [spellux](https://github.com/questoph/spellux) library.

Where to start?
~~~~~~~~~~~~~~~

👉 Check out the :doc:`your_first_agent` tutorial. You will learn how simple it can be!

👉 Dive into the :doc:`wiki` and become a master of agents.

Example agents
--------------

- :doc:`examples/greetings_agent`: Very simple agent for the first contact with the framework
- :doc:`examples/weather_agent`: Introducing :doc:`entities <wiki/core/entities>`
- :doc:`examples/llm_agent`: Introducing :doc:`Large Language Models (LLMs) <wiki/nlp/llm>`
- :doc:`examples/rag_agent`: Introducing :doc:`Retrieval Augmented Generation (RAG) <wiki/nlp/rag>`
- :doc:`examples/telegram_agent`: Introducing the :doc:`wiki/platforms/telegram_platform`
- :doc:`examples/github_agent`: Introducing the :doc:`wiki/platforms/github_platform`
- :doc:`examples/gitlab_agent`: Introducing the :doc:`wiki/platforms/gitlab_platform`
- :doc:`examples/web_crawl_agent`: Crawling websites and grounding answers with :doc:`wiki/utils/web_crawl`
