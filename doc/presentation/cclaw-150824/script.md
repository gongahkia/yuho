# Script for SMU CCLAW presentation 150824

## Introduction 
* Hello everyone, thank you for giving me this opportunity to present Yuho

## Brief introduction
* Gabriel
* Incoming Y2 computing and law student 
* Interests include bouldering and eating at ya kun kaya toast
* Friends with Zeming, who introduced me to vim in 2020 when i first started programming
* I now use doom emacs

## Preface
* I have little experience with language development, formal specification, and writing interpreters and transpilers
* A lot of the code in the Yuho repository is untested and not passing even in development
* Very much experimental and a work in progress
* I do not have a CS background nor do I have strong foundations so where I have used the wrong terms, I seek your guidance 
* Hopefully some of what I share today will be interesting feedback from LLB students

## Yuho v1 
* Yuho in its first iteration
* Target audience was LLB students, especially those entering from their first year 
* Many LLB friends shared with me that one of the larger hurdles they faced was being able to comprehend legalese, both in terms of statutes and common law rulings
* I chose the direct approach and sought to attack statutory provisions in the Penal Code
* It so happened that I had just finished a sem on Criminal Law which I really enjoyed, and at least in SMU Criminal Law seems to be a foundational mod that law students take in either sem 1 or 2, so that led to me focusing on Criminal Law
* So with that I defined the syntax for Yuho, which was 2 main products 
    * a DSL that law students could use to WRITE out statutory provisions in so as to better understand the composite elements of a statute 
    * transpilation outputs, the ones more applicable for the law students would have been Mermaid and JSON
        * Transpile a .yh file to a html file with a mermaid diagram and the Yuho code and the json

## Things I learnt while working on Yuho v1
* I wanted it to have a syntax close to Python for ease of readability
* But I also ended up fighting the tension of wanting its syntax to be easy to tokenize and parse
* One focus that I had was that I wanted to limit the number of keywords as far as possible so as to prevent complexity for law students
    * Struct can be any number of things from an enum to a dictionary (like a table in Lua or PHP)
    * Match case to replace all other conditional constructs (edge guarding wahoo)
* Another thing that I was quite troubled by while working on the mental modelling of Yuho was 
    * Exactly how rigid should I be making its syntax?
    * Initially I began with defining a container datatype called a statute outright
    * But I later retreated and reverted it to a struct because I wanted to give enough wiggleroom and flexibility for students to define any concept within a statute
    * Which would mean that in theory, they could define the entire penal code in Yuho
    * Just a preference thing
    * Another thing that’s a small quirk but was important to me was that I wanted Yuho to NOT follow the object oriented paradigm
    * I felt that classes and objects and the entire concept of inheritance would quickly convolute the focus that Yuho had a simple syntax even if it's true that OOP is the most ‘natural’ way to model complex situations
    * This is an assumption on my part and I might explore OOP as an alternative in the future 
    * Ended up choosing to somewhat follow functional languages in their syntax just for consistency 
* Fortunate enough to have some LLB friends test the syntax for me, and here is some of the feedback they shared with me (some being 8 people as of now)
    * Onboarding process was quite smooth and SURPRISINGLY syntax is relatively understandable 
    * They enjoyed the “refactoring” process which they had to go through, many first broke down a statute by defining the struct literal, then went back to define elements that could be represented within the struct definition, apparently that helped their understanding the most
    * HOWEVER, feedbacked that the static typing was confusing for them when writing struct definitions 
        * I had initially incorporated it with the hope that it would give clarity for what each field could be but in action it seemed to have convoluted the syntax
        * Served the purpose specifying where a type could either be a value or null (pass in Yuho)
    * Is there another way to represent such union types?
    * One thing I noticed was that many of them did not use the flexible struct syntax as I had hoped for or intended
    * Made me reflect on what exactly is a good way to represent the idea of containers / structs / records for the layman. Is there an even more intuitive way that it can be represented? 
    * Perhaps I was too boxed in being a programmer 
* On reflection, here were some of the issues with Yuho v1
    * One pressing issue that I was cognisant of when developing but that I had pushed to the back of my mind until Prof Alex Woon mentioned it was that the representation of statutes is still very coarse
        * Eg being that the definition section is literally still a string, it does not show any conditional logic and the law student still needs to figure out what’s going on for themselves
    * Takes a very Simple, rudimentary approach towards breaking down a statute
    * I wanted to include a live editor that would allow them to actively write Yuho code and see whether it actually transpiled to valid output but that never came to fruition
    * A more user-friendly interface was in order as well
    * I was also overly concerned with ensuring Yuho adhered to the ‘formal specifications’ I was told a language required (which is definitely important), but I neglected to focus on optimising Yuho for the usecase, which was to benefit student’s learning

## Yuho v2 
* Second iteration of Yuho that I’m still working on 
* Target audience is still somewhat focused on LLB students, but has expanded to the layman as well who wants to benefit from statutes
* Still focused on the Penal Code, but targeting the definition within each provision in particular 
* Regarding outputs, some LLB students (some being 6 of them), who shared that the mindmap from the web frontend was helpful, so I wanted to incorporate that in some way
* Very much experimental and a work in progress, but what I have so far is a transpiler that transpiles an already VALIDATED Yuho struct definition of a provision’s definition section into a
* Mermaid mindmap
* Mermaid flowchart (flowchart is more useful)
* Transpiler that after receiving a VALIDATED struct definition and a struct literal of an illustration, will return a 2 flowcharts, 
    * One showing the Highlighted Chosen path for that given situation
    * One showing the actual scenario as a flowchart

## Future plans
* Regarding validation logic, i've been playing around with some lexer-parser auto generators like Lex, Yacc and ANTLR with varying degrees of success 
* Possibly could incorporate both Yuho v1 and v2 together given that v2 just focuses on the definition element covered within v1 
* Hope to integrate the flowchart with a web frontend that allows stepping through
* One of my peers mentioned integrating an LLM exclusively trained on legal data and Yuho so as to automate the learning process for law students and to provide immediate advice
