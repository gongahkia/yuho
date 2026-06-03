# Legal Timeline Walkthrough

This walkthrough uses `Brown v. Board of Education` as a public legal-history demo for Euclid's current legal framing.

The demo is intentionally explicit: Euclid does not infer legal truth. It models the claims, facts, evidence, exhibits, and relationships that the author writes down, then makes the differences between two `.euclid` files visible.

## Sources Modeled

The example uses a small set of source-backed dates:

| Modeled event | Euclid date range | Source |
| --- | --- | --- |
| Topeka NAACP suit filed | `1951-02-01..1951-02-28` | [National Park Service](https://www.nps.gov/brvb/learn/historyculture/kansas.htm) says the Topeka NAACP filed suit in February 1951. |
| U.S. District Court denial | `1951-08-01..1951-08-31` | [National Park Service](https://www.nps.gov/brvb/learn/historyculture/kansas.htm) summarizes the August 1951 district-court ruling. |
| Supreme Court argument | `1952-12-09..1952-12-09` | [National Archives](https://www.archives.gov/milestone-documents/brown-v-board-of-education) transcript metadata lists the argument date. |
| Supreme Court reargument | `1953-12-08..1953-12-08` | [National Archives](https://www.archives.gov/milestone-documents/brown-v-board-of-education) transcript metadata lists the reargument date. |
| Brown decision | `1954-05-17..1954-05-17` | [National Archives](https://www.archives.gov/milestone-documents/brown-v-board-of-education) identifies the May 17, 1954 decision. |
| Brown II decree | `1955-05-31..1955-05-31` | [National Archives](https://www.archives.gov/milestone-documents/brown-v-board-of-education) summarizes the follow-up decree date. |

Month-only source facts are represented as month ranges instead of invented exact days.

## Files

The two narratives live under [`examples/legal/`](../examples/legal/):

```text
examples/legal/brown_plaintiffs.euclid
examples/legal/brown_board.euclid
```

Both files share the same `brown_case` timeline, core `fact` entities, and source-backed `evidence`/`exhibit` entities. They differ in the emphasis of the modeled `claim` entities and relationships:

* `brown_plaintiffs.euclid` foregrounds the equal-protection and harm claims that Brown accepted.
* `brown_board.euclid` foregrounds the district-court and board posture under the separate-but-equal doctrine.

Legal relationship labels are first-class validator metadata. `cites` is checked as `evidence -> claim/fact`, `supersedes` is checked as later source replacing earlier target, and `contradicts` remains an explicit modeled edge that warns when both sides appear on the same timeline.

## Check The Inputs

```console
$ euclid check examples/legal/brown_plaintiffs.euclid
warning: validation- examples/legal/brown_plaintiffs.euclid:96:1- contradiction on timeline brown_case: plaintiffs_equal_protection_claim contradicts board_separate_equal_claim

$ euclid check examples/legal/brown_board.euclid
warning: validation- examples/legal/brown_board.euclid:97:1- contradiction on timeline brown_case: district_court_denial contradicts plaintiffs_equal_protection_claim
```

## Diff The Narratives

```console
$ euclid diff examples/legal/brown_plaintiffs.euclid examples/legal/brown_board.euclid
```

Representative output:

```text
Timelines:
  (no differences)
  (no differences)
Entities:
  ~ changed board_separate_equal_claim
  ~ changed brown_decision
  ~ changed district_court_denial
  ~ changed plaintiffs_equal_protection_claim
  ~ changed plaintiffs_harm_claim
Relationships:
  + only in right brown_opinion_record -[cites]-> board_separate_equal_claim
  + only in right district_court_denial -[contradicts]-> plaintiffs_equal_protection_claim
  + only in right district_court_denial -[corroborates]-> board_separate_equal_claim
  - only in left brown_decision -[corroborates]-> plaintiffs_equal_protection_claim
  - only in left plaintiffs_equal_protection_claim -[contradicts]-> board_separate_equal_claim
  - only in left plaintiffs_harm_claim -[corroborates]-> plaintiffs_equal_protection_claim
```

The useful part is not that Euclid decides which side is right. The useful part is that narrative differences become source-level changes: claims change, cited positions change, and relationship edges move between files.

## Inspect Legal Reports

```console
$ euclid contradict examples/legal/brown_plaintiffs.euclid
Contradictions:
- plaintiffs_equal_protection_claim contradicts board_separate_equal_claim
  timelines: brown_case
  source evidence:
    - brown_opinion_record | citation=Brown v. Board of Education, 347 U.S. 483 | source=National Archives
  target evidence:
    - nps_case_history | citation=Brown v. Board of Education National Historical Park | source=National Park Service

$ euclid exhibits examples/legal/brown_plaintiffs.euclid
number,entity,description,timeline,start,end
Ex. 1,opinion_exhibit,National Archives copy of the Brown opinion,brown_case,1954-05-17,1954-05-17
```

## Export A Visual

```console
$ euclid export examples/legal/brown_plaintiffs.euclid -f svg -o brown-plaintiffs.svg
$ euclid export examples/legal/brown_board.euclid -f html -o brown-board.html
$ euclid export examples/legal/brown_plaintiffs.euclid --narrative plaintiffs -f json -o brown-plaintiffs-only.json
$ euclid diff examples/legal/brown_plaintiffs.euclid examples/legal/brown_board.euclid -f svg -o brown-diff.svg
$ euclid diff examples/legal/brown_plaintiffs.euclid examples/legal/brown_board.euclid -f html -o brown-diff.html
```

For the secondary historical and generative examples, see:

```text
examples/historical/ww2.euclid
examples/generative/lotr.euclid
```
