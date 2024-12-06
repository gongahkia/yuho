# Roadmap 

Things are happening at [`yuho_and_beyond`](./../archive/yuho_and_beyond/).

![](../asset/memes/roadrunner_skinamarink.jpg)

1. Yuho LSP
    1. Write a LSP that works for most major code editors
    2. Provides snippets, linting and syntax highlighting
    3. Flags errors that might arise from wrongful Yuho code

2. Yuho live editor
    1. an in-browser IDE 
        1. transpiles written yuho code live to a specified diagramatic output
        2. linting
        3. snippets and autocomplete
        4. provides decent error messages
    2. see [lawtodata](https://lawtodata.streamlit.app/) web application
    3. see [streamlit](https://streamlit.io/cloud) as platform to deploy app on
    4. see [L4's IDE](https://smucclaw.github.io/l4-lp/)
    5. see [ANTLR Lab](http://lab.antlr.org/) for a program that exposes a user-visible AST 
    6. see [L4 Google Sheets Extension](https://l4-documentation.readthedocs.io/en/latest/docs/quickstart-installation.html#getting-the-legalss-spreadsheet-working-on-your-computer) for a google suite extension that integrates a DSL

3. Yuho should be LLM powered
    1. Work out how to integrate a trained LLM that can read and validate Yuho
    2. Explore other usecases where an LLM would be useful
    3. Both front-end and back-end
    4. Consider [langchainlaw](https://github.com/nehcneb/langchainlaw/tree/main) integration for training a model
    5. Yuho as an intermediary language that makes understanding the logic of the law easier to learn for a given model
    6. LLM-powered service that transpiles existing legislation to Yuho lang
    7. Further applications could include a chatgpt or bert powered CHARGE GENERATION FORM that will receive a given statute and parse it to Yuho, then feeding that through a lang-chain powered model that puts the Yuho code into a formalised english form
    8. LLM-powered Chatbot
        1. Chatbot that can provide legal advice to the layman **and** explain law concepts clearly to students via Mermaid diagrams
        2. Yuho could be an intermediary language that provides sanitised input to easily train LLMs on SG Criminal Law cases
        3. **things to implement**
            1. `model_1`: train a model that takes in existing statutes and converts it to Yuho code
                1. Statute def *(plaintext)* --[`model_1`]--> Statute def *(Yuho struct)*
            2. `model_2`: train a model that takes in a statute as a yuho struct and a plaintext scenario and outputs the yuho struct for that scenario
                1. Statute def *(Yuho struct)* + Statute illustration / Sample scenario *(plaintext)* --[`model_2`]--> Statute illustration / Sample scenario *(Yuho struct)*
        4. Consider whether to use encoder/decoder or transformer model, see other available options
    9. see [legal-bert](https://huggingface.co/nlpaueb/legal-bert-base-uncased)
    10. see [scott](https://scott.intelllex.com/)
    11. see [ollama](https://ollama.com/library)

4. Form generation
    1. See [motoraccidents.lawnet](https://motoraccidents.lawnet.sg/) for reference on easy form creation 
    2. Consider implementation as a google docs or google sheets extension

5. Scratch-like web app to learn the law
    1. Scratch-like controls with drag and drop interface so different logical blocks can be rearranged and the struct updates live
    2. Is there a HTML element / Svelte frontend that can achieve the same flow-chart like Display without relying on Mermaid? *(ideally I would want HMR)*
    3. see [Svelteflow](https://svelteflow.dev/) for reactive diagrams and flowcharts
    4. see [Whyline](https://www.cs.cmu.edu/~NatProg/whyline.html) for dynamic sites that display logical evaluation of a given decision
    5. Allow user to ask "Why did" and "Why didn't" questions about a given output
        1. Users choose from a set of questions generated automatically via static and dynamic analyses, and the tool provides answers in terms of the runtime events that caused or prevented the desired output
    6. Consider implementing this in [Blockly](https://developers.google.com/blockly)

6. Uncategorised
    1. There are many assumptions made when we reason from one premise to another premise in the law, how far do we push this inquiry back?
        1. *eg. before even considering how a given a given statute should apply for a case, we should figure whether the given case can even be heard in the current court*
    2. See [CCLaw Sandbox](https://github.com/smucclaw) for inspiration