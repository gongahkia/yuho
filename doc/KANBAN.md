# Yuho v3.0 Kanban Board

Things actively being worked on.

## Backlog 🔙

1. 

## Doing ✍️

1. 

## Review 🗳️

1. 

## Done 👏

1. 

## Follow Up Actions

> See [here](https://docs.google.com/document/d/1LTxfNQ1bS9gfFlFkAGrGTDzjjhMmyWh7slpYRvE5KQY/edit?usp=drive_link) for follow up actions for class part or make a seperate repo

1. Can I implement a syntax that covers Tort law as well?
    * Plot out the architecture diagram first
        * Work out how to integrate a trained LLM that can read and validate Yuho
    * Consider completely redefining Yuho's syntax to cover the following features
        * simpler and easy to learn and write a tokenisor and parser, closer to Julia 
        * make the CLI tools easier to learn
    * Implement a syntax that covers 
        * common law rulings
        * statutory provisions
        * real logic so that CCLAW's edgecases in logic under point 4 can be covered
    * How these rulings would tie in to existing cases

1. Consider implementing [langchainlaw](https://github.com/nehcneb/langchainlaw/tree/main) and Yuho's editor as a [streamlit](https://streamlit.io/cloud) app
    1. see sample implementation [here](https://lawtodata.streamlit.app/)

2. See https://motoraccidents.lawnet.sg/ and https://github.com/smucclaw/ladder-diagram
    * Could Yuho provide a way for dynamic form generation *(even a glorified google form or execel sheet)* for specific statutes?
    * Try implementing sections from the [Road Traffic Act](https://sso.agc.gov.sg/SL/RTA1961-R20) and see if the generated flowchart is harder to parse
    * Integrate a transpiler to generate a HTML form or brainstorm other frontends that Lawyers can easily use and deploy siilar to `motoraccidents/quantum`
    * Integrate a transpiler that drafts emails and whatsapp messages informing clients of all possible outcomes, integrate an LLM for this portion
   
3. Regarding the interlinks between statutes
    * Many provisions, when they become more complex, have terms like “subject to” that logically connect different sections or entire statutes *(by way of providing explanation or exception for a given rule or term)*
    * Can I provide an example of how Yuho can represent 2 statutes interacting, both in `.yh` code and in Mindmap and Flowchart form?

4. Implement Prof How Khang's feedback *(15/08/2024)*
    * Any DSL that seeks to act as a reprentation of any domain of law needs to consider its purpose and scope
    * It is essential to consider both scope and purpose because providing an accurate representation of law that can make the implicit explicit then makes a DSL for the law useful for 
        * the lay-person trying to understand the law as a framework
        * LLMs that are being trained on a set number of inputs and outputs
    * Purpose-wise, we put law into code to make things that are implicit explicit since writing code inherently requires us to render out all assumptions that are made for a given situation
        * Can Yuho reach this state of representation for Criminal Law?
    * Scope-wise, how far back are we pushing the *(axiomatic)* point from which we are reasoning from? 
        * with regard to assumptions made
            * *eg. before even considering how a given a given statute should apply for a case, we should figure whether the given case can even be heard in the current court*
        * with regard to how granular and specific we are when breaking down a given statute
    * As an additonal consideration, what other aspects of law can Yuho seek to represent?
        * Given its flexible syntax, can we consider if it can accurately represent certain Tort cases which overlap with Criminal cases

5. Implement CCLAW's feedback *(15/08/2024)*
    * Need to iron out logical conondrums with how Yuho evaluates relational logic
        * *eg. S415 says "any person who...", how do we specify that "any person" does not include the`Party.Victim` or somewhere held as being in the same relationship as them, but specifically refers to the `Party.Accused` themselves*
    * It appears at first pass that defining object literals, then working your way to the class definition is always the more intuitive way of representing data
        * That said, is there a far more intuitive way of representing logic than through forcing definition of class templates?
        * Despite what I claim, Yuho's struct template and struct literal is just a glorified class object relationship

6. Afford exporting to multiple diagrammatic outputs
    * mermaid diagrams (all sorts)
    * ASCII diagrams for non-mermaid rendering interfaces
    * PLANTUML diagrams
    * graphviz
    * kroki
    * d2

## Products

1. Frontend WEB DISPLAY 
    * clicking-through feature to step through the highlighted path in a Mermaid flowchart
    * sidebar showing what each step fulfilled is like to achieve that highlighted path 
    * animating mermaid diagrams
        1. write a script that parses the mermaid file and assigns each start and destination arrow (descriptions within `[]`, split by `-->`)
        * this indice will later be referenced when deciding which arrow to color
            * `linkStyle <indiceThatIsTheArrowNumber> stroke:#77DD77,stroke-width:4px;`
        2. [get the images](https://blog.lmorchard.com/2023/01/03/mermaid-animations/)
        3. [invisible boxes](https://yairm210.medium.com/animating-mermaid-graphs-as-gifs-2ec8f3b24fbc) 

2. Frontend BROWSER EDITOR for Yuho code
    * in-browser IDE similar to [L4's IDE](https://smucclaw.github.io/l4-lp/)
    * produces a user-visible AST with legible error messages simialr to [ANTLR Lab](http://lab.antlr.org/)
    * transpiles written yuho code live to display a Mermaid diagram (see 3)
    * browser native LSP 
    * linting
    * snippets
    * provides decent error messages
    * consider using svelteflow

3. Yuho LSP
    * exported for other IDEs
        * VSCODE (as a browser extension)
        * Emacs
        * Vim

4. Yuho chatbot
    * Chatbot that can provide legal advice to the layman **and** explain law concepts clearly to students via Mermaid diagrams
    * Yuho as an intermediary language that provides sanitised input to easily train LLMs on SG Criminal Law cases
    * **things to implement**
        1. `model_1`: train a model that takes in existing statutes and converts it to Yuho code
            * Statute def *(plaintext)* --[`model_1`]--> Statute def *(Yuho struct)*
        2. `model_2`: train a model that takes in a statute as a yuho struct and a plaintext scenario and outputs the yuho struct for that scenario
            * Statute def *(Yuho struct)* + Statute illustration / Sample scenario *(plaintext)* --[`model_2`]--> Statute illustration / Sample scenario *(Yuho struct)*
    * see [legal-bert](https://huggingface.co/nlpaueb/legal-bert-base-uncased)
    * see [scott](https://scott.intelllex.com/)
    * see [ollama](https://ollama.com/library)

## Later

1. Checks under `./test`
    * right now only checking for syntax and enforcing basic conditional constructs
    * add files to dynamically generate tests for different statutes
    * integrate LLMs that are fed sanitised struct to see whether Yuho's internal logic and struct validity can be 'tested'
        * consider whether to use encoder/decoder or transformer model, see other avail options

2. Appealing UI/UX
    * intuitive controls so lawyers and law students *(no programming proficiency required)*
    * "right now you're showing how the sausage is made *(the nerdy programmer shit)*"
    * pitching Yuho to lawyers requires an easy to **access** and **use** frontend interface
    * provide 2 frontend products
        1. live editor for Yuho code that updates the mermaid diagram
            * see [L4 IDE](https://smucclaw.github.io/l4-lp/) for live editor that allows updating of diagrams
            * in terms of functionality and ease of use, see L4's approach via a [Google Sheets Extension](https://l4-documentation.readthedocs.io/en/latest/docs/quickstart-installation.html#getting-the-legalss-spreadsheet-working-on-your-computer) 
        2. scratch-like controls with drag and drop interface so different logical blocks can be rearranged and the struct updates live
            * is there a HTML element / Svelte frontend that can achieve the same flow-chart like Display without relying on Mermaid? *(ideally I would want HMR)*
            * see [Svelteflow](https://svelteflow.dev/) for reactive diagrams and flowcharts
        * retain the flowchart-style display to show all logical outcomes of a given offence as defined by the statute
        * add user input method that allows 'stepping-through' the flowchart for a given charge / **highlight** the logical path for A --> B, useful especially if the flowchart is very complex and nested
            * see [Whyline](https://www.cs.cmu.edu/~NatProg/whyline.html) for dynamic sites that display logical evaluation of a given decision
                * application in Yuho front-end
                    * allows users to ask "Why did" and "Why didn't" questions about a given output
                    * users choose from a set of questions generated automatically via static and dynamic analyses, and the tool provides answers in terms of the runtime events that caused or prevented the desired output
        * see [Enso](https://github.com/enso-org/enso/tree/develop?tab=readme-ov-file) for dynamic sites that provide accurate intuitive modelling of why a given statute operates the way it does
        * see [Tonto](https://matheuslenke.github.io/tonto-docs/) for how it models conceptual models textually
        * see [D2](https://github.com/terrastruct/d2) for a diagramming language as easy to read as markdown and mermaid
        * see [Kroki](https://kroki.io/) for the variety of transpilation outputs for a single textual representation

3. Comprehensive 
    * find edgecases Prof Alexandar Woon was talking about within the Penal Code *(generated by the amendments or not)*

4. Rework the following files per the new changes
    * `./README.md` for updates to Yuho's usage and status under > [IMPORTANT!]
    * `./doc/syntax.md` for updates to Yuho's syntax
    * `./example/sample*.yh` for updates to all Yuho example files with the updated syntax
    * `./grammer/` for updates to all files regarding Yuho's new grammer and syntax
    * `./src/main/` for updates to all files recursively *(`-r`)* within all folders in `./src` regarding changes to Yuho's syntax
    * `./src/seconday/` for updates to all Yuho transpilers for Yuho's new syntax
    * `./web/src` for updates to all files like `trans_*.py` regrading transpilation to Yuho's new syntax
    * `./web/dep/*` for updates to all files recursively within all folders in `./web/dep` regarding chanegs to Yuho's validated examples of how Yuho code is meant to look
    * `./web/front/index.html` for updates to the transpiled HTML frontend code
    * `./lsp/` for a complete rehaul of Yuho's LSP and to provide IDE-style syntax highlighting for any IDE I want Yuho to be supported in

5. Account for the *Explanations* under every section (*eg.* s415)
    * Add a new syntax keyword OR define a struct attribute under an existing struct to include these *Explanations* sections
    * Do I want to break down the terms and logic within these sections also?
    * Consider how these *Explanations* would be rendered on the existing Mindmap and Flowchart representations in mermaid

6. Future scope
    * expand Yuho's scope to cover **both** definition **and** the consequence punishment application sections (s416 - s420)
    * see how to represent them within `.yh` code first, include those in the `./examples/` folder
    * then determine what their transpiled output and diagramatic representation in `.mmd` would look like
    * identify common UNIQUE attributes shared by s416-s420 *(consequence punishment application sections)*
    * incorporate conditional logic (like AND OR) into those attributes and make as granular as possible
        * What other elements of a statute can I break up and specify logic within?
    * rethink Yuho's syntax to be more specific toward Criminal Law *(examine statutes within the Penal Code, what should we be representing?)*
    * can I represent detailed evaluation of a struct instance that includes BOTH the base definition *(eg. s415)* AND its detailed applications *(eg. s416-420)* within the same flowchart?

7. More development on fault element, physical element, defences
    * Further integrate the composite elements of Actus reus and Mens rea into Yuho's syntax and diagramatic representation?
        * Fault element
            * INTENTION
            * KNOWLEDGE
            * RASHNESS
            * NEGLIGENCE
        * Physical element
            * CAUSATION
            * CONCURRENCE
            * AUTOMATISM
            * ILLEGAL OMISSION
    * Include general and specific defences?
       * Shelve discussion of defences for now and add it below to future.md as additional thing to consider but inconsequential since statutes by default don't specify the defences of an offence
       * Perhaps can include it within the flowchart
    * Refer to Criminal Law notes google doc from Azfir's structure of inquiry as required