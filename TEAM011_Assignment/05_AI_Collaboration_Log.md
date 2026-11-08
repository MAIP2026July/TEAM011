# 08 · AI Collaboration Log: how AI was used to build this product

> I used AI heavily, and I disclose it here. I am a single-member team, so AI did much of the coding and testing that a larger team would share. My decisions set the direction. The main lesson is that **a good-looking result is not a correct one**: several key product changes came from checking AI work against evidence.

**Scope of this log.** The detailed entries below come from the Claude Code working session of 6–7 November 2026, which upgraded the prototype and drafted this submission. I reviewed the drafts, modified them where needed, and agree with the final content. Earlier AI use is described only as far as I can confirm it.

## Tools used

| Tool | Used for |
|---|---|
| **Claude / Claude Code (Anthropic)** | Used with Copilot on the Milestone 1 topic form and the first prototype. Then analyzing Milestone 1, the prototype and the example structure; finding gaps; writing the prototype upgrade; building the test set and evaluation; drafting this document pack and presentation deck |
| **GitHub Copilot (AI coding editor)** | Used on the Milestone 1 topic form, and in earlier development to create the Python project structure and modules, based on my faculty-approved PolicyGuard AI project context document, supplied as a PDF |
| **Gemini API (inside the product)** | Document reading, rule assessment, embeddings and rationale drafting |
| ChromaDB | Local vector store for the rulebook |
| Playwright with Chrome | Scripted end-to-end run of the app and screenshots |

## Where AI helped (by PM activity)

| Activity | How AI helped | My role |
|---|---|---|
| **Discovery / framing** | Compared Milestone 1 with the code and listed the gaps | I set the problem, users and scope in Milestone 1, and chose to fix the prototype before writing |
| **Decisions** | Presented options with trade-offs | I chose the output folder, setting, wedge, RAG design, test size, and recommendation |
| **Drafting** | Wrote first drafts of all documents and the deck | I set the scope and reviewed the claims |
| **Wireframing** | No separate design tool was used. Claude Code drafted the wireframe notes and captured the screenshots from the working app by script | I reviewed and accepted the wireframe notes and screenshots. The working prototype stands in as the wireframe, and the screens are mine to defend |
| **Prioritization** | Calculated RICE scores | I own the inputs and overrides |
| **Coding** | Wrote the evidence checks, RAG layer, scoring, UI and tests | I reviewed results and gave direction |
| **Synthetic data** | Generated 24 folders with planted defects | I chose the test size and the dev/holdout design |
| **Metrics and evaluation** | Built and ran the evaluation | I provided API access and required real results |
| **Economics** | Calculated scenarios by script | I chose the setting. The assumptions were proposed with AI and are not validated. I accepted the internal value case as the monetization model |
| **Risk review** | Linked risks to real test failures | I own the recommendation and launch blockers |

## Example prompts and workflows

**Prompt 1: framing (actual request, typing errors corrected)**
> "Please analyze the policyguard-ai project and project subject/context file. Based on given .md files 01 to 11, can you please create the similar .md files for me… Please ask me always for any ambiguity or decision making before creating all these .md files based on my project here."

*Outcome:* instead of drafting straight away, the AI analyzed the code and raised questions. That review exposed the gaps below, and it changed the task from "write documents" to "fix the product first".

**Workflow 2: structured decisions**
The AI asked 13 multiple-choice questions, each stating its trade-off. Examples: how to handle code gaps, what business setting to assume, how to build RAG, and how large the test set should be.

*Outcome:* I accepted most recommendations. I overrode one: the AI recommended a simple local index, and I chose **ChromaDB**.

**Workflow 3: fair evaluation**
Folders were split into dev and holdout sets. Holdout used different wording and date formats. It ran once, after the code was frozen, and its one false alarm was reported, not tuned away.

**Prompt 4: grounded prompt (inside the product)**
> In `backend/document_analyzer.py`: *"Check this document… against ONLY the rules below… Use 'unclear' when you cannot tell. Do not rely on outside knowledge."*

## Where AI was weak or wrong

Items 1–4 came from the earlier prototype and Milestone 1 work, and were a mix of AI and human errors. Items 5–12 occurred in the logged session. Items 13–16 came from checking the drafts against the Final Student Packet.

| # | What happened | Type | Found by |
|---|---|---|---|
| 1 | **Failed silently.** The first prototype gave **100/100** and **"Approved for Automated Renewal"** when AI analysis failed or no key was present. | Unsafe output | Claude Code review |
| 2 | **Crossed a product boundary.** The same prototype used "Automated Renewal" wording, although Milestone 1 says humans always decide. | Requirement drift | Claude Code review |
| 3 | **Claims did not match the code.** Milestone 1 described RAG, evidence and confidence indicators, but the code had none of them. | Gap between document and product | Claude Code review |
| 4 | **Test data contradicted the brief.** The "compliant" mock folder had a risk assessment dated before the application, which Milestone 1 calls an inconsistency. | Wrong test data | Claude Code review |
| 5 | **Passing with open findings.** New scoring let a folder with one major finding reach exactly 90 and be marked Pass, with "Recommend Renewal". | Logic error by AI | Claude Code testing |
| 6 | **Critical rule skipped.** Retrieval at 6 rules missed SIG-001 on 2 applications. Nothing in the dev result showed this: detection was still 14 of 14. | Hidden failure | Claude Code testing |
| 7 | **Risky default.** The AI-written UI pre-selected "Approve renewal", and the test script recorded an approval on a Hold folder. | Over-reliance by design | Claude Code testing |
| 8 | **False reassurance.** A green "No findings" appeared on a folder that was never analysed. | Misleading UI | Claude Code testing |
| 9 | **Invalid test run.** The free tier allowed only 20 requests a day, so an early run was cut short. Its low score reflected the quota, not the model. | Invalid result | Claude Code testing |
| 10 | **Wrong time estimate.** The AI estimated about 15 minutes for a run, then revised this to 35–40 minutes. | Overconfident estimate | Claude Code, on rechecking |
| 11 | **Version-specific failure.** The first evidence schema was rejected by the installed Gemini SDK. | Technical error by AI | Claude Code testing |
| 12 | **Model disagreed with itself.** On one scan, the model accepted a signature in one step and called it "a squiggle" in another. | Unstable AI judgment | Holdout evaluation |
| 13 | **Copied wording.** The AI used another team's example for structure, but sentences and phrasing carried over into its drafts. | Generic, borrowed output | Text comparison, when I asked for the packet check |
| 14 | **Unverified case lessons.** The case lessons were written from general knowledge, without my course material. | Possible invented facts | Claude Code disclosed it to me |
| 15 | **Wrong fact in a draft.** A draft of this log said 12 decision questions were asked. There were 13. | Wrong fact | Claude Code, on rechecking |
| 16 | **Missed requirements.** Working from another team's structure, the drafts had a 3-page Executive Summary, no deck, no launch checklist and no "what would you do differently" in the cases. | Requirement drift | My check against the packet |

## Human Corrections

Claude Code found and fixed most of the technical defects, during testing that I asked for. The first table shows what I decided or changed myself. The second shows the AI-found defects and the fixes I accepted.

**Decisions and changes I made**

| What we changed | Why we changed it | Judgment applied |
|---|---|---|
| Changed the task from "write the documents" to "fix the prototype first" | The documents had to describe a real product | Substance over a tidy report |
| Chose ChromaDB over the AI's recommended simple local index | A proper vector store is closer to production, and I accepted the extra dependency | Overrode an AI recommendation |
| Required the AI to ask me before any ambiguous decision | Choices about scope and evidence are mine | Kept the decisions with the PM |
| Required real results, and set the recommendation at Pilot, not scale | Synthetic evidence does not justify scaling | Conservative launch call |
| Added my own AI tool use to this log and to the contribution statement | Only I could supply that history | Honest disclosure |
| Had the drafts checked against the Final Student Packet, then chose which gaps to fix and how to package the work | The drafts followed another team's structure, not the course requirements | Requirement over convenience |
| Changed the setting to a US insurer and costed every people role at an onsite rate of US$150 an hour | The earlier rupee rates understated the cost of onsite analysts | Cost basis set by the PM |
| Confirmed the internal value case and accepted the open risks in the Risk Register | The packet says these decisions cannot go to AI | Ownership of monetization and risk |

**Fixes to AI-found defects**

| # | What changed | Why | Principle |
|---|---|---|---|
| 1 | Any failed analysis now gives **Not Scored** and no recommendation | Silence must not look like compliance | Fail safe over convenience |
| 2 | Renewal output is always a suggestion; the word "approved" is blocked in AI rationale | Milestone 1's human-in-the-loop promise | Product intent sets the boundary |
| 3 | Added RAG, evidence, confidence bands and human review | Documents must describe the real product | Fix the product, not just the wording |
| 4 | New test folders follow the Milestone 1 date rule | Tests must match the requirement | Requirement over existing data |
| 5 | Any open finding now blocks a Pass | A Pass must mean no open issue | Trust over a tidy score |
| 6 | Signature rules always run, and retrieval rose from 6 to 10 rules | A critical check must not depend on ranking | Reliability over elegance |
| 7 | The renewal decision now starts blank | The default must not nudge approval | Design against over-reliance |
| 8 | Unanalysed folders now show a warning instead of "No findings" | No false reassurance | Honest UI |
| 9 | Discarded the invalid run and changed model; evaluation now stops at a daily limit | Report only valid measurements | Evaluation discipline |
| 10 | Reported the corrected time to me | Plans should rest on real durations | Correct the record |
| 11 | Flattened the schema to suit the installed SDK | The code must run on the pinned version | Test on the real stack |
| 12 | Reported the false alarm, added repeatability as a pilot gate, and did not tune it away | Holdout must remain fair | Honest evidence over a perfect score |
| 13 | Rewrote the affected passages in project-specific wording | The work must not reuse another team's text | Academic integrity |
| 14 | Matched case names to the packet's list. The lessons stay my responsibility | Facts must be checked | Verification |
| 15 | Corrected the count | The log must be accurate | Accuracy |
| 16 | Cut the summary to 2 pages, and added the deck, checklist and case column | The packet sets the requirements | Requirement over structure |

## Final reflection

*Drafted with Claude Code; I agree with it.*

**Where AI accelerated PM work**
- Producing a working prototype that could be tested, not just described.
- Running a repeatable evaluation and economic scenarios quickly.
- Letting one person cover every role in a team assignment.

**Where AI could not replace PM reasoning**
- Choosing the problem and keeping humans as the decision-makers.
- Deciding to fix the product before writing about it.
- Deciding what evidence is sufficient, and recommending a pilot rather than a scale-up.

**Biggest lesson:** the riskiest failures were quiet. A 14-of-14 result hid a skipped critical rule. A perfect-looking score appeared when nothing had been analysed. **Checking how a result was produced matters as much as checking the result.**
