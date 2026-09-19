#!/usr/bin/env python3
"""Generate the retained v0.3 Singapore corpus from checked-in source material.

This is a deterministic repository maintenance tool.  The production corpus
query and evaluation paths remain Haskell-only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "library/penal_code/_raw/act.json"
BASE = ROOT / "research/singapore/corpus-v0.3"
MODULES = BASE / "modules"
SCENARIOS = BASE / "scenarios"
COVERAGE = ROOT / "research/singapore/SINGAPORE-CRIMINAL-LAW-COVERAGE-v0.3.json"
INDEX = ROOT / "research/singapore/CORPUS-INDEX.md"
GAPS = ROOT / "docs/rewrite/CORE-YUHO-v0.3-LANGUAGE-GAPS.md"

LANGUAGE_GAPS = [
    "missing_normative_or_deontic_construct",
    "missing_aggregate_or_sequence_construct",
    "missing_temporal_or_transitional_construct",
    "missing_participation_form",
    "missing_penalty_form",
    "missing_procedural_construct",
    "requires_evidential_assessment",
    "requires_judicial_interpretation",
    "source_unavailable_or_ambiguous",
    "outside_substantive_penal_code_scope",
]


def element(identifier: str, kind: str, quote: str) -> dict[str, str]:
    return {"id": identifier, "kind": kind, "quote": quote}


EXCEPTIONS = [
    {
        "id": "section76", "section": "76", "direct": [],
        "alternatives": [
            element("76-bound-by-law", "circumstance", "bound by law to do it"),
            element("76-justified-by-law", "circumstance", "justified by law in doing it"),
        ],
    },
    {
        "id": "section77", "section": "77",
        "direct": [element("77-judge", "circumstance", "done by a judge when acting judicially")],
        "alternatives": [
            element("77-lawful-power", "circumstance", "power which is given to the judge by law"),
            element("77-good-faith-power", "fault", "in good faith believes the power is given by law"),
        ],
    },
    {
        "id": "section78", "section": "78",
        "direct": [
            element("78-order-in-force", "circumstance", "judgment or order remains in force"),
            element("78-good-faith-jurisdiction", "fault", "in good faith believes that the court had jurisdiction"),
        ],
        "alternatives": [
            element("78-pursuant-judgment", "conduct", "done in pursuance of the judgment or order"),
            element("78-warranted-order", "conduct", "warranted by the judgment or order"),
        ],
    },
    {
        "id": "section83", "section": "83",
        "direct": [
            element("83-age-10-to-under-12", "circumstance", "child of or above 10 years and below 12"),
            element("83-insufficient-maturity", "circumstance", "not attained sufficient maturity of understanding to judge the nature and consequence of the conduct on that occasion"),
        ],
        "alternatives": [],
    },
    {
        "id": "section85-involuntary-nature-route", "section": "85",
        "direct": [
            element("85-intoxication", "circumstance", "by reason of the intoxication at the time of the act or omission"),
            element("85-did-not-know-conduct", "knowledge", "did not know what the person was doing"),
        ],
        "alternatives": [
            element("85-without-knowledge", "circumstance", "state of intoxication was caused without the knowledge of the person"),
            element("85-against-will", "circumstance", "state of intoxication was caused against the will of the person"),
        ],
    },
    {
        "id": "section87", "section": "87",
        "direct": [
            element("87-no-intent-death-grievous-hurt", "intention", "not intended to cause death or grievous hurt"),
            element("87-no-knowledge-likely-death-grievous-hurt", "knowledge", "not known to be likely to cause death or grievous hurt"),
            element("87-person-above-18", "circumstance", "person above 18 years of age"),
            element("87-consent", "circumstance", "given consent, whether express or implied, to suffer or risk the harm"),
        ],
        "alternatives": [],
    },
    {
        "id": "section94", "section": "94",
        "direct": [
            element("94-not-excluded-offence", "circumstance", "offence is not murder or an offence against the State punishable with death"),
            element("94-compelled-by-threats", "circumstance", "person is compelled to do it by threats"),
            element("94-instant-death-apprehension", "circumstance", "threats reasonably cause apprehension that instant death will otherwise be the consequence"),
        ],
        "alternatives": [],
    },
    {
        "id": "sections96-98-private-defence", "section": "96,97,98",
        "direct": [
            element("96-exercise-private-defence", "circumstance", "done in the exercise of the right of private defence"),
            element("97-protected-body-or-property", "circumstance", "defence of a body or qualifying property against a listed offence or attempt"),
            element("98-no-more-harm-than-necessary", "circumstance", "does not inflict more harm than reasonably necessary in the circumstances"),
            element("98-no-reasonable-public-authority-opportunity", "circumstance", "no reasonable opportunity to have recourse to protection of a public authority"),
        ],
        "alternatives": [],
    },
]


FAMILIES = [
    {
        "slug": "unlawful-assembly-membership", "offence": "unlawful-assembly-membership",
        "rule": "sections141-143", "sections": ["141", "142", "143"],
        "category": "public-order", "exception": "section76",
        "direct": [
            element("141-five-or-more", "circumstance", "assembly of 5 or more persons"),
            element("141-qualifying-common-object", "purpose", "common object is one of the objects in paragraphs (a) to (e)"),
            element("142-aware-unlawful-facts", "knowledge", "aware of facts which render the assembly unlawful"),
        ],
        "alternatives": [
            element("142-intentionally-joins", "conduct", "intentionally joins that assembly"),
            element("142-intentionally-continues", "conduct", "intentionally continues in that assembly"),
        ],
        "penalty": ("143", 2, "years", "unbounded"),
        "limitation": "The qualifying common object is externally supplied; Yuho does not infer it from group conduct.",
    },
    {
        "slug": "rioting", "offence": "rioting", "rule": "sections141-147",
        "sections": ["141", "146", "147"], "category": "public-order", "exception": "section76",
        "direct": [
            element("146-unlawful-assembly", "circumstance", "force or violence is used by an unlawful assembly or a member"),
            element("146-force-or-violence", "conduct", "force or violence is used"),
            element("146-common-object-prosecution", "purpose", "used in prosecution of the common object of the assembly"),
            element("146-member", "circumstance", "person is a member of the assembly"),
        ], "alternatives": [], "penalty": ("147", 7, "years", "caning:24"),
        "limitation": "The section 147 imprisonment-and-caning terms are presented as a candidate statutory penalty, not an imposed sentence.",
    },
    {
        "slug": "false-information-public-servant", "offence": "false-information-public-servant", "rule": "section182",
        "sections": ["182"], "category": "public-servants-and-justice", "exception": "section77",
        "direct": [
            element("182-gives-information", "conduct", "gives to a public servant any information"),
            element("182-knows-or-believes-false", "knowledge", "knows or believes the information to be false"),
            element("182-intended-or-likely-use", "intention", "intending or knowing it likely to cause use of lawful power"),
            element("182-injury-or-improper-action", "circumstance", "use of power to injury or annoyance, or an act or omission that would differ if true facts were known"),
        ], "alternatives": [], "penalty": ("182", 2, "years", "unbounded"),
        "limitation": "The causal and public-servant power classifications are supplied rather than inferred.",
    },
    {
        "slug": "obstructing-public-servant", "offence": "obstructing-public-servant", "rule": "section186-individual",
        "sections": ["186"], "category": "public-servants-and-justice", "exception": "section76",
        "direct": [
            element("186-voluntary-obstruction", "conduct", "voluntarily obstructs"),
            element("186-public-servant", "circumstance", "a public servant"),
            element("186-public-functions", "circumstance", "in discharge of the public servant's public functions"),
            element("186-individual", "circumstance", "offender is an individual"),
        ], "alternatives": [], "penalty": ("186", 6, "months", "2500"),
        "limitation": "This branch is limited to section 186(1)(a), concerning an individual.",
    },
    {
        "slug": "disappearance-of-evidence", "offence": "disappearance-of-evidence", "rule": "section201",
        "sections": ["201"], "category": "public-servants-and-justice", "exception": "section78",
        "direct": [
            element("201-offence-committed", "circumstance", "knowing or having reason to believe that an offence has been committed"),
            element("201-screening-intent", "intention", "intention of screening the offender from legal punishment"),
        ],
        "alternatives": [
            element("201-causes-evidence-disappear", "conduct", "causes evidence of commission of the offence to disappear"),
            element("201-gives-false-information", "conduct", "gives information respecting the offence which the person knows or believes to be false"),
        ], "penalty": None,
        "limitation": "Section 201's tiered penalty depends on the predicate offence and is not represented by the current candidate-term form.",
    },
    {
        "slug": "obstruction-of-justice", "offence": "obstruction-of-justice", "rule": "section204A",
        "sections": ["204A"], "category": "public-servants-and-justice", "exception": "section77",
        "direct": [element("204A-act-tendency", "conduct", "does an act that has a tendency to obstruct, prevent, pervert or defeat the course of justice")],
        "alternatives": [
            element("204A-knowledge", "knowledge", "knowing that the act is likely to obstruct, prevent, pervert or defeat the course of justice"),
            element("204A-intention", "intention", "intending to obstruct, prevent, pervert or defeat the course of justice"),
        ], "penalty": ("204A", 7, "years", "unbounded"),
        "limitation": "The tendency and course-of-justice classifications are supplied open-textured inputs.",
    },
    {
        "slug": "public-nuisance", "offence": "public-nuisance", "rule": "sections268-290-base",
        "sections": ["268", "290"], "category": "public-health-safety-and-nuisance", "exception": "section83",
        "direct": [
            element("268-common-impact", "circumstance", "common injury, danger or annoyance to the public or qualifying obstruction, danger or annoyance to users of a public right"),
            element("290-not-otherwise-punishable", "circumstance", "case is not otherwise punishable by the Code"),
        ],
        "alternatives": [
            element("268-does-act", "conduct", "does any act"),
            element("268-illegal-omission", "conduct", "is guilty of an illegal omission"),
        ], "penalty": ("290", None, None, "2000"),
        "limitation": "Only the base section 290(a) fine branch is represented; knowledge and repeat-conviction branches are deferred.",
    },
    {
        "slug": "culpable-homicide", "offence": "culpable-homicide", "rule": "sections299-304-knowledge",
        "sections": ["299", "304"], "category": "human-body", "exception": "sections96-98-private-defence",
        "direct": [element("299-causes-death", "consequence", "causes death by doing an act")],
        "alternatives": [
            element("299-intent-death", "intention", "intention of causing death"),
            element("299-intent-likely-fatal-injury", "intention", "intention of causing bodily injury likely to cause death"),
            element("299-knowledge-likely-death", "knowledge", "knowledge that the act is likely to cause death"),
        ], "penalty": None,
        "limitation": "Section 304 has different terms for intention and knowledge routes, including forms the candidate-term fragment cannot express; no candidate penalty is selected for this combined offence graph.",
    },
    {
        "slug": "rash-causing-death", "offence": "rash-causing-death", "rule": "section304A-rash",
        "sections": ["304A"], "category": "human-body", "exception": "section85-involuntary-nature-route",
        "direct": [
            element("304A-causes-death", "consequence", "causes the death of a person"),
            element("304A-rash-act", "fault", "doing a rash act"),
            element("304A-not-culpable-homicide", "circumstance", "act does not amount to culpable homicide"),
        ], "alternatives": [], "penalty": ("304A", 5, "years", "unbounded"),
        "limitation": "This executable branch is rashness only; the separate negligent branch and its two-year maximum are indexed but deferred.",
    },
    {
        "slug": "outraging-modesty", "offence": "outraging-modesty", "rule": "section354-subsection1",
        "sections": ["354"], "category": "human-body", "exception": "section87",
        "direct": [
            element("354-assault-or-criminal-force", "conduct", "assaults or uses criminal force to a person"),
            element("354-outrage-modesty", "consequence", "thereby outrages the modesty of that person"),
            element("354-victim-not-under-14-branch", "circumstance", "base subsection (1) branch rather than subsection (2) child-victim branch"),
        ],
        "alternatives": [
            element("354-intention", "intention", "intending to outrage modesty"),
            element("354-knowledge", "knowledge", "knowing it likely that modesty will be outraged"),
        ], "penalty": ("354", 3, "years", "unbounded"),
        "limitation": "The model is limited to subsection (1); caning and the subsection (2) child-victim branch are contextual.",
    },
    {
        "slug": "cheating-by-personation", "offence": "cheating-by-personation", "rule": "sections416-419",
        "sections": ["416", "419"], "category": "property-and-deception", "exception": "section85-involuntary-nature-route",
        "direct": [element("416-cheats", "conduct", "cheats")],
        "alternatives": [
            element("416-pretends-other-person", "conduct", "pretending to be some other person"),
            element("416-substitutes-person", "knowledge", "knowingly substituting one person for another"),
            element("416-represents-other-identity", "conduct", "representing a person as someone other than that person really is"),
        ], "penalty": ("419", 5, "years", "unbounded"),
        "limitation": "The underlying cheating classification is supplied; this model does not duplicate the complete section 415 graph.",
    },
    {
        "slug": "forgery", "offence": "forgery", "rule": "sections463-465",
        "sections": ["463", "465"], "category": "documents-records-and-identity", "exception": "section78",
        "direct": [element("463-false-document-record", "conduct", "makes a false document or electronic record or part thereof")],
        "alternatives": [
            element("463-damage-injury-intent", "intention", "intent to cause damage or injury to the public or any person"),
            element("463-claim-title-intent", "intention", "intent to support any claim or title"),
            element("463-part-property-contract-intent", "intention", "intent to cause a person to part with property or enter a contract"),
            element("463-fraud-intent", "intention", "intent to commit fraud or that fraud may be committed"),
        ], "penalty": ("465", 4, "years", "unbounded"),
        "limitation": "False-document status and the selected statutory intent are supplied classifications.",
    },
    {
        "slug": "using-forged-record", "offence": "using-forged-record", "rule": "section471",
        "sections": ["471", "465"], "category": "documents-records-and-identity", "exception": "section76",
        "direct": [
            element("471-uses-as-genuine", "conduct", "uses as genuine a document or electronic record"),
            element("471-forged-status", "circumstance", "document or electronic record is forged"),
        ],
        "alternatives": [
            element("471-fraudulently", "fault", "fraudulently uses as genuine"),
            element("471-dishonestly", "fault", "dishonestly uses as genuine"),
        ],
        "secondary_alternatives": [
            element("471-knows-forged", "knowledge", "knows the document or record to be forged"),
            element("471-reason-believe-forged", "knowledge", "has reason to believe the document or record to be forged"),
        ], "penalty": ("465", 4, "years", "unbounded"),
        "limitation": "Section 471 applies section 465's manner of punishment; aggravated forgery provisions are not selected.",
    },
    {
        "slug": "criminal-intimidation", "offence": "criminal-intimidation", "rule": "sections503-506-base",
        "sections": ["503", "506"], "category": "intimidation-nuisance-and-reputation", "exception": "section94",
        "direct": [element("503-threat-injury", "conduct", "threatens another with qualifying injury to person, reputation or property")],
        "alternatives": [
            element("503-intent-alarm", "intention", "intent to cause alarm to that person"),
            element("503-compel-act", "intention", "intent to cause an act not legally bound to be done as the means of avoiding the threat"),
            element("503-compel-omission", "intention", "intent to cause omission of an act legally entitled to be done as the means of avoiding the threat"),
        ], "penalty": ("506", 2, "years", "unbounded"),
        "limitation": "Only the base section 506 punishment branch is represented; aggravated threats are deferred.",
    },
    {
        "slug": "defamation", "offence": "defamation", "rule": "sections499-500-bounded",
        "sections": ["499", "500"], "category": "intimidation-nuisance-and-reputation", "exception": "section94",
        "direct": [
            element("499-makes-publishes-imputation", "conduct", "makes or publishes an imputation concerning a person"),
            element("499-reputation-harm", "consequence", "imputation harms the reputation of that person"),
            element("499-no-statutory-exception", "circumstance", "none of section 499's statutory exceptions applies"),
        ],
        "alternatives": [
            element("499-intends-harm", "intention", "intending to harm reputation"),
            element("499-knows-harm", "knowledge", "knowing the imputation will harm reputation"),
            element("499-reason-believe-harm", "knowledge", "having reason to believe the imputation will harm reputation"),
        ], "penalty": ("500", 2, "years", "unbounded"),
        "limitation": "The ten statutory exceptions and their explanations are not expanded; non-application is an explicit supplied classification.",
    },
]


CHAPTERS = [
    (1, 5, "chapter-1-preliminary", "preliminary"),
    (6, 52, "chapter-2-general-explanations", "general-part"),
    (53, 75, "chapter-3-punishments", "punishments"),
    (76, 106, "chapter-4-general-exceptions", "general-exceptions"),
    (107, 120, "chapter-5-abetment-and-conspiracy", "participation"),
    (121, 140, "chapters-6-and-7-state-and-armed-forces", "state-and-armed-forces"),
    (141, 160, "chapter-8-public-tranquillity", "public-order"),
    (161, 190, "chapters-9-and-10-public-servants-and-lawful-authority", "public-servants-and-justice"),
    (191, 229, "chapter-11-false-evidence-and-public-justice", "public-servants-and-justice"),
    (230, 267, "chapters-12-and-13-coins-stamps-weights", "currency-stamps-and-measures"),
    (268, 294, "chapters-14-and-15-public-health-and-religion", "public-health-safety-and-nuisance"),
    (295, 377, "chapter-16-human-body", "human-body"),
    (378, 462, "chapter-17-property", "property-and-deception"),
    (463, 489, "chapter-18-documents-and-records", "documents-records-and-identity"),
    (490, 502, "chapters-19-to-21-contract-marriage-defamation", "intimidation-nuisance-and-reputation"),
    (503, 510, "chapter-22-intimidation-insult-and-annoyance", "intimidation-nuisance-and-reputation"),
    (511, 512, "chapter-23-attempts", "attempt"),
]


EXISTING_EXECUTABLE = {
    "23", "24", "79", "80", "81", "82", "84", "107", "109", "319", "321", "323",
    "336", "339", "341", "351", "352", "378", "379", "403", "405", "406", "410", "411",
    "415", "417", "425", "426", "441", "447", "511",
}


EXISTING_MODELS = {
    **{number: "research/singapore/section-84-pilot/statutory-definitions/section323-section379-definitions.yh"
       for number in ("23", "24", "319", "321", "323", "378", "379")},
    "84": "research/singapore/section-84-pilot/surface/section84.yh",
    **{number: "research/singapore/abetment-routes-pilot/section107-routes-theft.yh"
       for number in ("107", "109")},
    "511": "research/singapore/attempt-pilot/section511-theft-attempt.yh",
    **{number: "research/singapore/offence-corpus-pilot/modular-cheating-mischief.yh"
       for number in ("415", "417", "425", "426")},
    **{number: "research/singapore/research-release/singapore-criminal-law-release.yh"
       for number in ("79", "80", "81", "82", "336", "339", "341", "351", "352",
                       "403", "405", "406", "410", "411", "441", "447")},
}


EXISTING_SCENARIO_DIRS = {
    **{number: "research/singapore/section-84-pilot/statutory-definitions/scenarios"
       for number in ("23", "24", "319", "321", "323", "378", "379")},
    "84": "research/singapore/section-84-pilot/hurt-offence/scenarios",
    **{number: "research/singapore/abetment-routes-pilot/scenarios" for number in ("107", "109")},
    "511": "research/singapore/attempt-pilot/scenarios",
    **{number: "research/singapore/offence-corpus-pilot/scenarios/cheating" for number in ("415", "417")},
    **{number: "research/singapore/offence-corpus-pilot/scenarios/mischief" for number in ("425", "426")},
    **{number: "research/singapore/research-release/scenarios/rash-endangerment" for number in ("80", "336")},
    **{number: "research/singapore/research-release/scenarios/wrongful-restraint" for number in ("81", "339", "341")},
    **{number: "research/singapore/research-release/scenarios/assault" for number in ("351", "352")},
    **{number: "research/singapore/research-release/scenarios/misappropriation" for number in ("79", "403")},
    **{number: "research/singapore/research-release/scenarios/criminal-breach-of-trust" for number in ("82", "405", "406")},
    **{number: "research/singapore/research-release/scenarios/receiving-property" for number in ("410", "411")},
    **{number: "research/singapore/research-release/scenarios/criminal-trespass" for number in ("441", "447")},
}


EXISTING_INVALID_SCENARIOS = {
    "research/singapore/section-84-pilot/hurt-offence/scenarios/12_missing_section334.yh",
    "research/singapore/section-84-pilot/hurt-offence/scenarios/13_missing_post2022.yh",
    "research/singapore/section-84-pilot/hurt-offence/scenarios/15_missing_section323a.yh",
    "research/singapore/section-84-pilot/statutory-definitions/scenarios/09_hurt_derived_assignment.yh",
    "research/singapore/section-84-pilot/statutory-definitions/scenarios/15_theft_derived_assignment.yh",
    "research/singapore/section-84-pilot/statutory-definitions/scenarios/21_unreachable_assignment.yh",
    "research/singapore/section-84-pilot/statutory-definitions/scenarios/22_missing_reachable.yh",
}


DEFINITION_ONLY = {
    "6", "7", "8", "9", "10", "11", "12", "17", "19", "20", "21", "22", "22A", "25",
    "26", "26A", "26B", "26C", "26D", "26E", "26F", "26G", "26H", "27", "28", "29", "29A",
    "29B", "30", "31", "31A", "32", "33", "34", "35", "36", "37", "38", "40", "41", "42",
    "43", "44", "44A", "45", "46", "47", "48", "49", "50", "51", "53", "72", "120A", "120B",
}


def section_key(value: str) -> tuple[int, str]:
    match = re.match(r"(\d+)(.*)", value)
    if not match:
        return (10_000, value)
    return (int(match.group(1)), match.group(2))


def chapter_for(number: str) -> tuple[str, str]:
    numeric = section_key(number)[0]
    for lower, upper, chapter, category in CHAPTERS:
        if lower <= numeric <= upper:
            return chapter, category
    return "saved-export-structural-parent-unknown", "uncategorised"


def quote(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def requirement_parts(family: dict) -> tuple[list[dict], list[list[dict]]]:
    direct = list(family["direct"])
    groups = []
    for key in ("alternatives", "secondary_alternatives"):
        values = family.get(key, [])
        if values:
            groups.append(values)
    return direct, groups


def render_exception(item: dict) -> str:
    rows = [f"  general-exception x:{item['id']} rule r:{item['id']} program p:{item['id']} path section{item['section'].replace(',', '-')} sections {item['section']} {{"]
    for current in item["direct"] + item["alternatives"]:
        rows.append(f"    element {current['kind']} f:{current['id']} quote q:{current['id']};")
    members = [f"f:{current['id']}" for current in item["direct"]]
    if item["alternatives"]:
        alt = ", ".join(f"f:{current['id']}" for current in item["alternatives"])
        rows.append(f"    any g:{item['id']}-alternatives ({alt});")
        members.append(f"g:{item['id']}-alternatives")
    if len(members) >= 2:
        rows.append(f"    all g:{item['id']}-requirements ({', '.join(members)});")
    rows.append("  }")
    return "\n".join(rows)


def render_family_model(family: dict, include_exceptions: bool) -> str:
    model_id = ("SingaporePenalCodeCorpusV03ResearchPrototype-v1" if include_exceptions else
        "SingaporePenalCodeCorpusV03" + "".join(part.title() for part in family["slug"].split("-")) + "ResearchPrototype-v1")
    all_elements = family["direct"] + family.get("alternatives", []) + family.get("secondary_alternatives", [])
    quotes = []
    for known_family in FAMILIES:
        quotes.extend(f'    quote q:{item["id"]} "{quote(item["quote"])}";'
            for item in known_family["direct"] + known_family.get("alternatives", [])
            + known_family.get("secondary_alternatives", []))
    for exception in EXCEPTIONS:
        quotes.extend(f'    quote q:{item["id"]} "{quote(item["quote"])}";'
            for item in exception["direct"] + exception["alternatives"])
    lines = [
        "// Generated from the checked-in Penal Code act.json; bounded research expressions only.",
        f"model {model_id} {{", "  variant SuppliedProofStatus-v1;", "  jurisdiction Singapore;",
        "  purpose research_prototype;", "  request C03;", "  policy 2026-09-13 1024;", "",
        "  provenance {",
        '    source src:pc-v03 source_text "library/penal_code/_raw/act.json and corresponding saved statute.yh";',
        '    source src:corpus-v03 synthetic_status "research/singapore/corpus-v0.3 synthetic classifications";',
        *quotes, "  }", "", "  annotations { burden section107 defence legal balance_of_probabilities; }",
        "  scope-assumptions {",
        f"    scope-assumption a:bounded-{family['rule']}-expression for o:{family['offence']};",
        "  }", "",
    ]
    direct, groups = requirement_parts(family)
    section_clause = " sections " + ",".join(family["sections"])
    lines.append(f"  offence o:{family['offence']} rule r:{family['rule']} program p:{family['rule']} path {family['rule']}{section_clause} {{")
    for item in all_elements:
        lines.append(f"    element {item['kind']} f:{item['id']} quote q:{item['id']};")
    members = [f"f:{item['id']}" for item in direct]
    for index, group in enumerate(groups, 1):
        group_id = f"g:{family['rule']}-alternative-{index}"
        lines.append(f"    any {group_id} ({', '.join('f:' + item['id'] for item in group)});")
        members.append(group_id)
    lines.append(f"    all g:{family['rule']}-requirements ({', '.join(members)});")
    lines.extend(["  }", ""])
    if include_exceptions:
        for exception in EXCEPTIONS:
            lines.extend([render_exception(exception), ""])
    else:
        attached = next(item for item in EXCEPTIONS if item["id"] == family["exception"])
        lines.extend([render_exception(attached), ""])
    lines.extend(["  outputs {", f"    {family['slug'].replace('-', '_')}_final r:{family['rule']};", "  }"])
    if family["penalty"]:
        provision, prison, unit, fine = family["penalty"]
        terms = []
        if prison is not None:
            terms.append(f"imprisonment term:{family['slug']}-prison minimum not-stated maximum {prison} {unit};")
        if isinstance(fine, str) and fine.startswith("caning:"):
            terms.append(f"caning term:{family['slug']}-caning minimum not-stated maximum {fine.split(':', 1)[1]} strokes;")
        elif fine is not None:
            terms.append(f"fine term:{family['slug']}-fine currency SGD minimum not-stated maximum {fine};")
        combination = "all-of" if isinstance(fine, str) and fine.startswith("caning:") else "one-or-more-of"
        term_expression = (terms[0] if len(terms) == 1 else
            f"{combination} term:{family['slug']} {{ {' '.join(terms)} }}")
        lines.extend(["", "  candidate-penalties {",
            f"    candidate pen:section{provision}-{family['slug']} for offence o:{family['offence']} source src:pc-v03 provision {provision} {{ {term_expression} }}",
            "  }"])
    lines.extend(["", "  limitations {",
        '    "All classifications and applicability assumptions are externally supplied";',
        f'    "{quote(family["limitation"])}";',
        '    "Candidate penalty terms are contextual candidates, not imposed sentences";',
        '    "No evidence, guilt, conviction, acquittal, liability, sentence or court disposition is determined";',
        "  }", "}", ""])
    return "\n".join(lines)


def exception_assignments(exception: dict, mode: str, false_index: int = 0) -> dict[str, str]:
    values = exception["direct"] + exception["alternatives"]
    result = {item["id"]: "proved" for item in values}
    if mode == "defeat":
        return result
    if mode == "unresolved":
        result[values[false_index % len(values)]["id"]] = "unresolved(not_determined)"
        return result
    for item in exception["alternatives"]:
        result[item["id"]] = "not_proved"
    if exception["direct"]:
        result[exception["direct"][false_index % len(exception["direct"])]["id"]] = "not_proved"
    return result


def offence_assignments(family: dict, mode: str) -> dict[str, str]:
    direct, groups = requirement_parts(family)
    values = {item["id"]: "proved" for item in direct}
    for group in groups:
        for item in group:
            values[item["id"]] = "not_proved"
        values[group[0]["id"]] = "proved"
    if mode == "alternative":
        for group in groups:
            if len(group) > 1:
                values[group[0]["id"]] = "not_proved"
                values[group[1]["id"]] = "proved"
    elif mode == "conduct-false":
        target = next((item for item in direct if item["kind"] in ("conduct", "consequence")), direct[0])
        values[target["id"]] = "not_proved"
    elif mode == "fault-false":
        if groups:
            for item in groups[0]:
                values[item["id"]] = "not_proved"
        else:
            values[direct[-1]["id"]] = "not_proved"
    elif mode == "unresolved":
        target = next((item for item in direct if item["kind"] in ("conduct", "consequence")), direct[0])
        values[target["id"]] = "unresolved(not_determined)"
    return values


def render_scenario(family: dict, index: int, name: str, offence_mode: str, exception_mode: str) -> str:
    exception = next(item for item in EXCEPTIONS if item["id"] == family["exception"])
    values = offence_assignments(family, offence_mode)
    values.update(exception_assignments(exception, exception_mode, index))
    lines = ["// Synthetic supplied classifications; no evidence or judicial outcome is determined.",
        "scenario C03 for SingaporePenalCodeCorpusV03ResearchPrototype-v1 {",
        f"  analyse o:{family['offence']};", f"  assume a:bounded-{family['rule']}-expression;"]
    for identifier, status in values.items():
        lines.append(f"  f:{identifier} = {status};")
    lines.extend(["}", ""])
    return "\n".join(lines)


SCENARIO_MATRIX = [
    ("01_satisfied_primary", "primary", "not-established"),
    ("02_satisfied_alternative", "alternative", "not-established"),
    ("03_conduct_not_proved", "conduct-false", "not-established"),
    ("04_fault_or_circumstance_not_proved", "fault-false", "not-established"),
    ("05_material_unresolved", "unresolved", "not-established"),
    ("06_exception_defeats", "primary", "defeat"),
    ("07_exception_unresolved", "primary", "unresolved"),
    ("08_exception_cannot_rescue_failed_offence", "conduct-false", "defeat"),
]


def render_module(family: dict, include_exceptions: bool) -> str:
    module_name = f"singapore.penal-code.{family['slug']}"
    source = f"{family['slug']}.yh"
    lines = [f"statutory-module {module_name} version 1.0.0 {{"]
    if include_exceptions:
        lines.append("  export model SingaporePenalCodeCorpusV03ResearchPrototype-v1;")
        for exception in EXCEPTIONS:
            lines.append(f"  export general-exception x:{exception['id']};")
    lines.append(f"  export offence o:{family['offence']};")
    if family["penalty"]:
        lines.append(f"  export candidate-penalty pen:section{family['penalty'][0]}-{family['slug']};")
    lines.extend([f'  source-model "{source}";', "}", ""])
    return "\n".join(lines)


def render_host() -> str:
    lines = ["modular-model SingaporeCriminalLawCorpus-v0.3 {", '  module-root "modules";']
    for family in FAMILIES:
        lines.append(f"  import singapore.penal-code.{family['slug']} version 1.0.0 as {family['slug'].replace('-', '_')};")
    base_alias = FAMILIES[0]["slug"].replace("-", "_")
    lines.extend(["", f"  use model {base_alias}::SingaporePenalCodeCorpusV03ResearchPrototype-v1;"])
    for family in FAMILIES:
        alias = family["slug"].replace("-", "_")
        lines.append(f"  use offence {alias}::o:{family['offence']};")
        if family["penalty"]:
            lines.append(f"  use candidate-penalty {alias}::pen:section{family['penalty'][0]}-{family['slug']};")
    for exception in EXCEPTIONS:
        lines.append(f"  use general-exception {base_alias}::x:{exception['id']};")
    lines.append("")
    for family in FAMILIES:
        lines.append(f"  attach {base_alias}::x:{family['exception']} to offence {family['slug'].replace('-', '_')}::o:{family['offence']};")
    lines.extend(["}", ""])
    return "\n".join(lines)


CASE_SPECS = [
    ("case-public-order-and-justice", [
        "unlawful-assembly-membership", "unlawful-assembly-membership", "rioting", "obstruction-of-justice"], True),
    ("case-person-harm-v03", ["culpable-homicide", "rash-causing-death", "outraging-modesty"], False),
    ("case-documents-and-intimidation", ["forgery", "forgery", "using-forged-record", "criminal-intimidation"], True),
    ("case-actor-exception-isolation-v03", ["public-nuisance", "rash-causing-death", "culpable-homicide", "obstructing-public-servant"], False),
]


def family_by_slug(slug: str) -> dict:
    return next(item for item in FAMILIES if item["slug"] == slug)


def render_case(case_id: str, slugs: list[str], shared: bool) -> str:
    roles = [f"role:actor-{index + 1}" for index in range(len(slugs))]
    actors = [f"actor:person-{index + 1}" for index in range(len(slugs))]
    lines = ["// Ordered independent technical allegations; no aggregate judicial status.",
        f"analysis-case case:{case_id} model \"modular-singapore-criminal-law-corpus-v0.3.yh\" {{"]
    for role, actor in zip(roles, actors):
        lines.append(f"  bind {role} to {actor};")
    shared_id = None
    shared_input = None
    if shared:
        first = family_by_slug(slugs[0])
        shared_element = first["direct"][0]
        shared_id = "fact:shared-" + first["slug"]
        shared_input = shared_element["id"]
        lines.append(f"  supplied-fact {shared_id} kind {shared_element['kind']} subject {actors[0]} target o:{first['offence']} status proved reason \"synthetic explicitly shared primitive classification\";")
    for index, (slug, role) in enumerate(zip(slugs, roles)):
        family = family_by_slug(slug)
        effective_role = roles[0] if shared and slug == slugs[0] else role
        exception = next(item for item in EXCEPTIONS if item["id"] == family["exception"])
        values = offence_assignments(family, "primary")
        values.update(exception_assignments(exception, "not-established", index))
        lines.extend(["", f"  allegation a:{slug}-{index + 1} analyse offence o:{family['offence']} for {effective_role} {{",
            f"    assume a:bounded-{family['rule']}-expression;"])
        if shared and slug == slugs[0] and shared_input is not None:
            lines.append(f"    bind-fact {shared_id} to input f:{shared_input};")
            values.pop(shared_input, None)
        for identifier, status in values.items():
            lines.append(f"    f:{identifier} = {status};")
        lines.append("  }")
    lines.extend(["}", ""])
    return "\n".join(lines)


def structural_state(section: dict) -> str:
    value = (section.get("marginal_note") or "").lower()
    if "repeal" in value or "reserved" in value:
        return "repealed_or_reserved"
    return "unknown"


def language_gap(number: str, category: str, classification: str) -> str | None:
    if classification in {"executable_research", "definition_only"}:
        return None
    if number in {"201", "304"}:
        return "missing_penalty_form"
    if classification == "executable_partial":
        return "requires_judicial_interpretation"
    if category == "punishments":
        return "missing_penalty_form"
    if category in {"participation", "attempt"}:
        return "missing_participation_form"
    if category == "public-servants-and-justice":
        return "missing_procedural_construct"
    if category in {"preliminary", "general-part"}:
        return "missing_normative_or_deontic_construct"
    return "requires_judicial_interpretation"


def executable_mapping() -> dict[str, dict]:
    result = {}
    for family in FAMILIES:
        paths = [f"research/singapore/corpus-v0.3/scenarios/{family['slug']}/{name}.yh" for name, *_ in SCENARIO_MATRIX]
        for section in family["sections"]:
            result.setdefault(section, {"models": [], "scenarios": [], "cases": [], "families": [], "constructs": set(), "exceptions": set(), "penalties": set()})
            row = result[section]
            row["models"].append(f"research/singapore/corpus-v0.3/modules/{family['slug']}.yh")
            row["scenarios"].extend(paths)
            row["families"].append(family["slug"])
            row["constructs"].update(["offence", "all", "any", "general-exception-attachment"])
            row["exceptions"].add(family["exception"])
            if family["penalty"]:
                row["penalties"].add(f"section{family['penalty'][0]}-{family['slug']}")
    for case_id, slugs, _ in CASE_SPECS:
        for slug in set(slugs):
            family = family_by_slug(slug)
            for section in family["sections"]:
                result[section]["cases"].append(f"research/singapore/corpus-v0.3/{case_id}.yh")
    return result


def existing_mapping(number: str) -> tuple[list[str], list[str]]:
    model = EXISTING_MODELS[number]
    directory = ROOT / EXISTING_SCENARIO_DIRS[number]
    scenarios = [relative for path in sorted(directory.glob("*.yh"))
        if (relative := path.relative_to(ROOT).as_posix()) not in EXISTING_INVALID_SCENARIOS]
    return [model], scenarios


def cross_references(text: str, valid: set[str]) -> list[dict]:
    values = []
    seen = set()
    pattern = r"\bsections?\s+([0-9]{1,3}[A-Z]?(?:\s*(?:,|and|or|to)\s*[0-9]{1,3}[A-Z]?)*)"
    for match in re.finditer(pattern, text, flags=re.IGNORECASE):
        for raw_target in re.findall(r"[0-9]{1,3}[A-Z]?", match.group(1), flags=re.IGNORECASE):
            target = raw_target.upper()
            if target in seen:
                continue
            seen.add(target)
            values.append({"kind": "statutory_reference", "raw": f"section {raw_target}",
                "target": f"penal-code:{target}" if target in valid else None,
                "resolution": "resolved" if target in valid else "unresolved"})
    return values


def generate_coverage() -> dict:
    raw = json.loads(RAW.read_text())
    sections = raw["sections"]
    valid = {section["number"].upper() for section in sections}
    mapped = executable_mapping()
    rows = []
    for section in sections:
        number = section["number"].upper()
        chapter, category = chapter_for(number)
        state = structural_state(section)
        mapping = mapped.get(number)
        if mapping:
            classification = "executable_partial"
            models = sorted(set(mapping["models"]))
            scenarios = sorted(set(mapping["scenarios"]))
            cases = sorted(set(mapping["cases"]))
            constructs = sorted(mapping["constructs"])
            exceptions = sorted(mapping["exceptions"])
            penalties = sorted(mapping["penalties"])
            limitations = [next(f["limitation"] for f in FAMILIES if number in f["sections"])]
            review = "authored_research_unreviewed"
        elif number in EXISTING_EXECUTABLE:
            classification = "executable_research"
            models, scenarios = existing_mapping(number)
            cases = []
            constructs = ["registered-existing-haskell-model"]
            exceptions, penalties = [], []
            limitations = ["Executable mapping is retained from the bounded Haskell research corpus; consult the model-specific limitation text."]
            review = "qualified_reviewed" if number == "84" else "authored_research_unreviewed"
        elif number in DEFINITION_ONLY:
            classification = "definition_only"
            models, scenarios, cases, constructs = [], [], [], ["saved-definition"]
            exceptions, penalties = [], []
            limitations = ["Structurally indexed definition or General Part concept; not independently executable in v0.3."]
            review = "legacy_saved_unreviewed"
        elif state == "repealed_or_reserved":
            classification = "repealed_or_reserved"
            models, scenarios, cases, constructs, exceptions, penalties = [], [], [], [], [], []
            limitations = ["Saved heading represents the provision as repealed or reserved."]
            review = "legacy_saved_unreviewed"
        else:
            classification = "saved_source_unmodelled"
            models, scenarios, cases, constructs, exceptions, penalties = [], [], [], [], [], []
            limitations = ["Saved structural text exists, but no authoritative Haskell executable research rule is registered."]
            review = "legacy_saved_unreviewed"
        gap = language_gap(number, category, classification)
        rows.append({
            "instrument_id": "singapore:penal-code-1871",
            "structural_parent": chapter,
            "provision_path": number,
            "provision_id": f"penal-code:{number}",
            "heading": section.get("marginal_note") or "",
            "structural_state": state,
            "source_reference": f"library/penal_code/_raw/act.json#{section.get('anchor_id', '')}",
            "quotation_reference": next((f"library/penal_code/{path.name}/statute.yh" for path in ROOT.glob(f"library/penal_code/s{section['number']}_*") if path.is_dir()), None),
            "cross_references": cross_references(" ".join(
                [section.get("text", "")] + [item.get("text", "") for item in section.get("sub_items", [])]), valid),
            "subject_category": category,
            "coverage_classification": classification,
            "executable_model_ids": models,
            "core_constructs": constructs,
            "scenario_paths": scenarios,
            "scenario_count": len(scenarios),
            "case_paths": cases,
            "case_count": len(cases),
            "definitions_consumed": [],
            "definitions_exported": [number] if classification == "definition_only" else [],
            "general_exceptions_attached": exceptions,
            "participation_support": number in {"107", "108", "109", "120A", "120B"},
            "attempt_support": number == "511",
            "candidate_penalties": penalties,
            "temporal_support": "authored_applicability_only" if classification.startswith("executable") else "none",
            "review_status": review,
            "language_gap": gap,
            "limitations": limitations,
        })
    classes = Counter(row["coverage_classification"] for row in rows)
    chapters = Counter(row["structural_parent"] for row in rows)
    categories = Counter(row["subject_category"] for row in rows)
    return {
        "schema": "yuho.singapore-criminal-law-coverage/v0.3",
        "instrument": {"id": "singapore:penal-code-1871", "title": raw["title"],
            "saved_source": "library/penal_code/_raw/act.json",
            "saved_source_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
            "chapter_assignment_basis": "bounded section-range corpus classification; saved export omits chapter headings",
            "legal_currency": "not_determined"},
        "closed_classifications": ["executable_research", "executable_partial", "structural_only", "definition_only", "cross_reference_only", "saved_source_unmodelled", "repealed_or_reserved", "outside_current_scope", "unknown"],
        "closed_language_gaps": LANGUAGE_GAPS,
        "summary": {"provisions": len(rows), "by_classification": dict(sorted(classes.items())),
            "by_chapter": dict(sorted(chapters.items())), "by_category": dict(sorted(categories.items())),
            "new_offence_families": len(FAMILIES), "total_offence_families": 11 + len(FAMILIES),
            "new_scenarios": len(FAMILIES) * len(SCENARIO_MATRIX) + 9,
            "total_singapore_scenarios": 177 + len(FAMILIES) * len(SCENARIO_MATRIX) + 9,
            "total_general_exceptions": 5 + len(EXCEPTIONS),
            "total_candidate_penalties": 9 + sum(1 for family in FAMILIES if family["penalty"]),
            "total_cases": 12 + 4},
        "provisions": rows,
    }


def render_index(coverage: dict) -> str:
    summary = coverage["summary"]
    family_rows = []
    for family in FAMILIES:
        penalty = "none (unsupported form)" if not family["penalty"] else f"s {family['penalty'][0]} candidate"
        family_rows.append(
            f"| {family['slug']} | {', '.join('s ' + value for value in family['sections'])} | "
            f"8 | {family['exception']} | {penalty} | {family['limitation']} |")
    classes = "\n".join(
        f"| `{name}` | {count} |" for name, count in summary["by_classification"].items())
    categories = "\n".join(
        f"| `{name}` | {count} |" for name, count in summary["by_category"].items())
    chapters = "\n".join(
        f"| `{name}` | {count} |" for name, count in summary["by_chapter"].items())
    return f"""# Singapore Criminal Law Research Corpus v0.3

This index is generated from [`SINGAPORE-CRIMINAL-LAW-COVERAGE-v0.3.json`](SINGAPORE-CRIMINAL-LAW-COVERAGE-v0.3.json) by `scripts/generate_singapore_corpus_v03.py`. Edit the generator and canonical coverage inputs, not the counts below.

Structural indexing, executable research coverage and legal review are separate. The saved Penal Code export does not determine legal currency. Every execution uses authored assumptions and externally supplied classifications; Yuho does not assess evidence or determine guilt, conviction, acquittal, liability, sentence or court disposition.

## Inventory summary

- Saved Penal Code provision rows: **{summary['provisions']}**.
- Executable offence families: **{summary['total_offence_families']}** (15 added in v0.3).
- Valid Singapore scenario files: **{summary['total_singapore_scenarios']}** (129 added in v0.3: 120 offence scenarios and 9 typed-rule showcases).
- Executable general-exception families: **{summary['total_general_exceptions']}**.
- Candidate-penalty declarations: **{summary['total_candidate_penalties']}**.
- Analysis cases: **{summary['total_cases']}**.
- Distinct Penal Code provision rows connected to executable models: **{summary['by_classification'].get('executable_research', 0) + summary['by_classification'].get('executable_partial', 0)}**; with the contextual Evidence Act s 107 anchor, the authored instrument/provision total is **{summary['by_classification'].get('executable_research', 0) + summary['by_classification'].get('executable_partial', 0) + 1}**.

Counts use distinct authored family identities, file-based valid scenarios, distinct exception definitions and distinct candidate declarations. Repeated statuses, parser refusals, raw statute files and contextual citations do not increase these totals.

The requested 100-authored-anchor target is therefore short by **{100 - (summary['by_classification'].get('executable_research', 0) + summary['by_classification'].get('executable_partial', 0) + 1)}**. The remaining saved rows were not promoted merely to meet a quota: 55 are structurally recognised definitions or General Part concepts without standalone Haskell execution, and 414 remain saved-source-unmodelled.

### Coverage classification

| Classification | Provisions |
|---|---:|
{classes}

### Subject category

| Category | Provisions |
|---|---:|
{categories}

### Structural parent

| Bounded chapter/range classification | Provisions |
|---|---:|
{chapters}

Chapter assignments are bounded section-range classifications because the saved export omits chapter-heading records.

## New executable families

| Family | Provision anchors | Scenarios | Attached exception | Candidate penalty | Executable boundary |
|---|---|---:|---|---|---|
{chr(10).join(family_rows)}

The reusable v0.3 module host is [`corpus-v0.3/modular-singapore-criminal-law-corpus-v0.3.yh`](corpus-v0.3/modular-singapore-criminal-law-corpus-v0.3.yh). Each family has an exact-version manifest and independently authored source under `corpus-v0.3/modules/`. Eight scenarios per family cover established, alternative-route, material not-proved, unresolved and exception interactions.

## Core v0.2 showcases and cases

- `corpus-v0.3/showcases/typed-section83-age.yh`: supplied integer age comparison plus supplied maturity classification.
- `corpus-v0.3/showcases/typed-unlawful-assembly-cardinality.yh`: five typed people and a three-valued `at-least 5` group condition.
- `corpus-v0.3/showcases/typed-property-and-fine.yh`: finite existential property relation and exact SGD minor-unit comparison.
- Four v0.3 cases cover public order/justice, person/harm, documents/intimidation and actor-specific exception isolation. Allegations remain independent and cases have no aggregate status.

## Querying the corpus

```sh
yuho corpus summary
yuho corpus list --category property-and-deception
yuho corpus show penal-code:84
yuho corpus check
yuho corpus coverage --format json
yuho corpus graph --format json --output inventory.json
yuho corpus graph --category human-body --format svg --output human-body.svg
```

From another working directory, append `--corpus-root /path/to/yuho`. Complete inventory SVG output is intentionally refused above 120 nodes; use JSON or a chapter/category/provision filter.

## Coverage meanings

- `executable_research`: retained, runnable Haskell research model.
- `executable_partial`: runnable bounded expression with material doctrine explicitly omitted.
- `definition_only`: structurally identified definition or General Part concept, not a standalone offence result.
- `saved_source_unmodelled`: saved text indexed but not executable.
- `repealed_or_reserved`: only used when the saved structure expressly marks that state.

Review status is a separate field. A saved or executable row is not automatically qualified-reviewed. See [`../../docs/rewrite/CORE-YUHO-v0.3-LANGUAGE-GAPS.md`](../../docs/rewrite/CORE-YUHO-v0.3-LANGUAGE-GAPS.md) for the coarse language-gap audit.
"""


def render_gaps(coverage: dict) -> str:
    counts = Counter(row["language_gap"] for row in coverage["provisions"] if row["language_gap"])
    total = sum(counts.values())
    rows = "\n".join(
        f"| `{name}` | {count} |" for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])))
    return f"""# Core Yuho v0.3 corpus language-gap audit

This is a generated corpus audit against the bounded Core Yuho v0.3 release language. The canonical inputs are the {coverage['summary']['provisions']} rows in [`../../research/singapore/SINGAPORE-CRIMINAL-LAW-COVERAGE-v0.3.json`](../../research/singapore/SINGAPORE-CRIMINAL-LAW-COVERAGE-v0.3.json). Normative positions, richer candidate sanctions and explicit responsibility routes close representation gaps only where saved material already supports a responsible authored model.

## Method and boundary

Exactly one primary language-gap category is assigned to each structurally saved provision that is not fully covered by an `executable_research` row or a `definition_only` row. The {total} assignments below are coarse triage based on the saved provision category and known executable limits. They do not say that a syntax extension alone would make a legally responsible model: provision-level interpretation and research remain necessary. Null gap values mean only that this audit does not identify a blocking language gap for that row.

| Primary gap | Affected provision rows |
|---|---:|
{rows}

The closed taxonomy also reserves `missing_aggregate_or_sequence_construct`, `missing_temporal_or_transitional_construct`, `requires_evidential_assessment`, `source_unavailable_or_ambiguous` and `outside_substantive_penal_code_scope`; none is used as a primary row classification in this saved Penal Code inventory. Those concepts remain real global limitations.

## Ranked implications for the final milestone

1. `requires_judicial_interpretation` has the largest affected set and high legal significance, but it is not chiefly a language defect. The final milestone should improve display and limitation auditing, not automate interpretation.
2. `missing_procedural_construct` affects public-justice provisions and is legally significant with high design cost. Criminal procedure and court disposition remain intentionally out of scope; no broad procedural calculus is recommended for the bounded release.
3. `missing_participation_form` is medium-sized and high significance. Existing s 107, conspiracy and s 511 slices remain usable; broader derivative and group responsibility should stay deferred unless one minimal construct resolves several reviewed provisions.
4. `missing_penalty_form` includes caning, death/life forms and predicate-offence-dependent terms. Candidate penalties are presentation-only and never sentences. A small additive term vocabulary may be considered, but sentencing logic remains out of scope.
5. `missing_normative_or_deontic_construct` affects a smaller General Part set. Core v0.3 can represent finite required, prohibited and permitted positions, but these eight rows remain unmodelled because the saved corpus does not support replacing their jurisdictional and interpretive questions with syntax alone.

## Global gaps not counted as primary rows

- Legal currency, commencement, retroactivity, savings and continuing conduct are not automatically selected.
- Narrative fact extraction, credibility, evidential sufficiency and open-textured classification remain externally supplied.
- Rule priority is explicit authored technical priority; it does not infer legal hierarchy.
- The saved structural export omits chapter-heading records and does not establish current law.
- Yuho does not produce guilt, conviction, acquittal, liability, sentence or criminal-procedure disposition.

Further judicial interpretation, procedure and sentencing extensions are optional future research rather than blockers to operating the bounded authored corpus.
"""


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def generate() -> None:
    for index, family in enumerate(FAMILIES):
        write(MODULES / f"{family['slug']}.yh", render_family_model(family, index == 0))
        write(MODULES / f"singapore.penal-code.{family['slug']}@1.0.0.yh", render_module(family, index == 0))
        for scenario_index, (name, offence_mode, exception_mode) in enumerate(SCENARIO_MATRIX):
            write(SCENARIOS / family["slug"] / f"{name}.yh",
                render_scenario(family, scenario_index, name, offence_mode, exception_mode))
    write(BASE / "modular-singapore-criminal-law-corpus-v0.3.yh", render_host())
    for case_id, slugs, shared in CASE_SPECS:
        write(BASE / f"{case_id}.yh", render_case(case_id, slugs, shared))
    write(COVERAGE, json.dumps(generate_coverage(), ensure_ascii=False, sort_keys=True,
        separators=(",", ":")) + "\n")
    write(INDEX, render_index(generate_coverage()))
    write(GAPS, render_gaps(generate_coverage()))


def check() -> None:
    expected = json.dumps(generate_coverage(), ensure_ascii=False, sort_keys=True,
        separators=(",", ":")) + "\n"
    if not COVERAGE.exists() or COVERAGE.read_text(encoding="utf-8") != expected:
        raise SystemExit("coverage artifact is stale; run generator")
    if not INDEX.exists() or INDEX.read_text(encoding="utf-8") != render_index(generate_coverage()):
        raise SystemExit("generated corpus index is stale; run generator")
    if not GAPS.exists() or GAPS.read_text(encoding="utf-8") != render_gaps(generate_coverage()):
        raise SystemExit("generated language-gap audit is stale; run generator")
    for index, family in enumerate(FAMILIES):
        expected_files = {
            MODULES / f"{family['slug']}.yh": render_family_model(family, index == 0),
            MODULES / f"singapore.penal-code.{family['slug']}@1.0.0.yh": render_module(family, index == 0),
        }
        for scenario_index, (name, offence_mode, exception_mode) in enumerate(SCENARIO_MATRIX):
            expected_files[SCENARIOS / family["slug"] / f"{name}.yh"] = render_scenario(
                family, scenario_index, name, offence_mode, exception_mode)
        for path, content in expected_files.items():
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"generated corpus file is stale: {path.relative_to(ROOT)}")
    if (BASE / "modular-singapore-criminal-law-corpus-v0.3.yh").read_text(encoding="utf-8") != render_host():
        raise SystemExit("generated modular corpus host is stale")
    for case_id, slugs, shared in CASE_SPECS:
        path = BASE / f"{case_id}.yh"
        if not path.exists() or path.read_text(encoding="utf-8") != render_case(case_id, slugs, shared):
            raise SystemExit(f"generated corpus case is stale: {path.relative_to(ROOT)}")
    print(f"Singapore corpus v0.3 generation check: {len(FAMILIES)} families, {len(FAMILIES) * len(SCENARIO_MATRIX)} scenarios, 524 coverage rows")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    check() if args.check else generate()


if __name__ == "__main__":
    main()
