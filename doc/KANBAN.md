# Yuho v3.0 Kanban Board

Things actively being worked on.

## Backlog 🔙

1. Edit SYNTAX.md and fully brainstorm complete set of keywords for Yuho
    1. AND, OR, NOT, CAUSES, TEST, REQUIRE, IF, ELSE, ELSEIF, RULING, PRECEDENT, ALL, NONE, ONE, MORE THAN ONE, ZERO, ()
    2. Syntax must be 
        1. simple to learn and write
        2. simple to read
        3. easy to tokenise, parse and interpret
        4. be able to represent common law rulings and statutes
        5. general enough to represent both criminal law and tort, as well as common law rulings
        6. all keywords are CAPITALISED by default for ease of reading
            * "Normalisation" results in documents that are faster and more accurate to read and understand 
        7. all keywords should aim to be familar to lawyers and the layperson and not too technical to avoid a steep learning curve
    3. Language inspirations
        1. Python
        2. Julia
        3. Nim
2. Logic engine
    1. Implement the Espresso-IISOJS npm libarry for heuristic minimiation of single-output boolean functions myself in python or whatever language I choose to write this in, probably just use Python for simplicity
    1. Can represent everything as truth values first
    2. Can evaluate those truth values
    3. Handles
        1. Boolean minimization
            1. As applied in *Poh Yuan Nie v Public Prosecutor [2022] SGCA 74* in Meng's presentation to me on 13/09/24
            2. A more complex statement should evaluate to a less complex one
                1. eg. `"Driving while intoxicated" IS NOT NOT NOT NOT NOT AN OFFENCE` = `"Driving while intoxicated" IS AN OFFENCE`
                2. eg. `"Entering the premises without permission" IF AND ONLY IF "breaking a window"` = `"Breaking a window" -> "Entering the premises without permission"`
                3. eg. `"Carrying a concealed weapon" AND "Committing theft" IS AN OFFENCE` = `"Committing theft" IS AN OFFENCE` and `"Carrying a concealed weapon" IS AN OFFENCE` 
                4. eg. `"Selling prohibited substances" IS AN OFFENCE AND IS NOT AN OFFENCE` == CONTRADICTION and will be flagged
                5. eg. `NOT "Assaulting a police officer" IF AND ONLY IF "Acting in self-defense"` = `"Acting in self-defense" -> NOT "Assaulting a police officer"`
        2. Contradiction flagging
        3. Variable substitution
            1. `(A and B) or (C and D and E)`, assuming we define `E in terms of C` which looks like `E = ! C` = `(A and B) or (C and D and not C)`
            2. now imagine E is "property" and C is defined as what is NOT property OR property's actual definition
            3. also this has a contradiction inside!
            4. simplification of boolean circuits is super relevant because it means we don't even need to waste resources validating D
            5. this means we have dropped from 5 cardinals to 2 cardinals
            6. also implement recursive definitions that will render the evaluation of statutes easier 
                1. eg. cheating s415 has the word dishonestly, wrongful gain and wrongful loss, defined in s23 and 24 respectively
        4. eliminating logic redundancy
        5. ignoring don't care terms and can't happen terms
    4. Allows for expressing statutes in terms of formal logic
        1. Per *Normalized legal drafting and the query method*
        2. Elimination of contradiction
        3. Simplification of complex legalese
        4. Simplification of nonsensical obiter and ratio
    5. Can dynamically generate a truth table from specified truth values and their relationships in any propositional formula presented
        1. TRUTH VALUES are replaced by statutes and its subdivisions
    6. Flags logical contradictions and fallacies
    7. Validates whether a given statement is logically coherent or not
    8. look into SAT solving and other formal methods to identify logical fallacies and issues with logic
3. Add all examples of sample Yuho code in the ./example file directory, 
    1. Represent the Spandeck test in Yuho for tort duty of care *(type of harm, threshold requirement and 2 stages of proximity and public policy considerations)*
    2. Represent old UK tests in Yuho for tort duty of care
    3. Add focus on whether the relationship shared between kinds of harm caused 
    4. Could the transpiler generate a degree_of_liability represented as a float?
    5. Interlinks between statutes
        1. Complex provisions have terms like “subject to” that logically connect different sections or entire statutes *(by way of providing explanation or exception for a given rule or term)*
        2. Provide an example of how Yuho can represent 2 statutes interacting
        3. Or remove this entire follow up action Or move it to FUTURE.md
4. Add the logic for the tokenisor, parser and interpreter in ./src file directory
5. Add proper tests that are runnable within Alloy or find another framework to run tests in
6. Brainstorm transpilation outputs for Yuho
    1. Diagrammatic outputs
        1. Mermaid diagrams, primarily with flowcharts
        2. [Ladder diagrams](https://github.com/smucclaw/ladder-diagram) 
        3. ASCII diagrams
        4. PLANTUML diagrams
        5. graphviz
        6. kroki
        7. d2
    * Transpile to a diagramatic representation similar to something Wong Weng Meng has achieved with his react application that shows the multiple pathways that are possible 
    * INCLUDE a similar field below *(generated dynamically by traversing all paths one can take)* that shows ALL POSSIBLE paths that the reading of a given statute can take, similar to the below image
    * purpose of this would be to 
        * convert ambigious within-sentence syntax into an unambigious between-sentence syntax
        * disambiguiting the relevant aspects of within-sentence syntax

![](../asset/reference/normalising_legal_drafting_1.png)
![](../asset/reference/normalising_legal_drafting_2.png)
![](../asset/reference/normalising_legal_drafting_3.png)
![](meng_proto_react_1.png)
![](meng_proto_react_2.png)
![](meng_proto_react_3.png)

7. Edit README.md to more accurately reflect Yuho's purpose
    1. Include an ASCII architecture diagram 
    2. Include a mermaid architecture diagram
    3. Benefits of a DSL is that code makes all things explicit while the law features many assumptions that are implicit
    4. Yuho as a DSL benefits from the law as code mindset by rendering these assumptions in detail
    5. Yuho's usecases
        1. purpose would be for law students to identify defective logic, charges and rulings when applying statutes
        2. purpose would be for lawyers, lawmakers and drafters to avoid wasting precious court time rationalilising or applying obiter and judgements that make little sense
    6. Research
        1. research cannons of interpretation and construction in law and those that are relevant for the implementation of DSLs and heuristic minimalisation 
        2. eg.
            1. harmonious construction
            2. rule against surplusage
            3. etc...
8. Create a suite of Yuho CLI tools
    1. Make them easy to install, learn and use
    2. References for decent CLI tools
        1. Rust Cargo
        2. Python Pip
        3. FZF
        4. Git

## Doing ✍️

1. 

## Review 🗳️

1. 

## Done 👏

1. 

> [!WARNING]
> FUA To move everything here to `ROADMAP.md` once done updating plans on this document

## Move to `ROADMAP.md` for future plans

* Yuho LSP
    * Write a LSP that works for most major code editors
    * Provides snippets, linting and syntax highlighting
    * Flags errors that might arise from wrongful Yuho code
* Yuho live editor
    * see [lawtodata](https://lawtodata.streamlit.app/) web application
    * see [streamlit](https://streamlit.io/cloud) as platform to deploy app on
* Yuho should be LLM powered
    * Work out how to integrate a trained LLM that can read and validate Yuho
    * Explore other usecases where an LLM would be useful
    * Both front-end and back-end
    * Consider [langchainlaw](https://github.com/nehcneb/langchainlaw/tree/main) integration for training a model
    * Yuho as an intermediary language that makes understanding the logic of the law easier to learn for a given model
    * LLM-powered service that transpiles existing legislation to Yuho lang
    * Further applications could include a chatgpt or bert powered CHARGE GENERATION FORM that will receive a given statute and parse it to Yuho, then feeding that through a lang-chain powered model that puts the Yuho code into a formalised english form
* Form generation
    * See [motoraccidents.lawnet](https://motoraccidents.lawnet.sg/) for reference on easy form creation 
    * Consider implementation as a google docs or google sheets extension
* Uncategorised
    * There are many assumptions made when we reason from one premise to another premise in the law, how far do we push this inquiry back?
        * *eg. before even considering how a given a given statute should apply for a case, we should figure whether the given case can even be heard in the current court*
    * See [CCLaw Sandbox](https://github.com/smucclaw) for inspiration

> [!WARNING]
> FUA to finish sorting and simplifying all this information under the relevant fields above

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