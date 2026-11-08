# 10 · Presentation Plan: leadership review format

Presenter: **Joydev Pain** (single-member team). Slides: `03_Presentation_Deck.pdf`. The order follows the packet's recommended structure. The timings assume 10 minutes, but the packet sets no limit, so adjust them once the faculty confirms one.

| # | Time | Packet step | Slide | What to say |
|---|---|---|---|---|
| 1 | 0:00–0:50 | Problem and business stakes | **Audit gaps surface too late** | "Every policy folder must survive an audit. People check them one at a time, so an auditor or a renewal often finds the gap first." |
| 2 | 0:50–1:40 | Target user and workflow | **Why the analyst, and the two decisions** | "Meera sits where the problem starts: she is the first to see a gap, and carries the blame if she misses one. I am improving two decisions: what to do with each finding, and the renewal decision." |
| 3 | 1:40–2:30 | Why AI, and why now | **Scripts read names; this work needs reading** | "A file-name script found 8 of 30 defects. Multimodal models and structured output now make quoted evidence practical at about 2.5 cents a folder. I am **not** automating sign-off or renewal." |
| 4 | 2:30–3:10 | Product concept and MVP | **One folder, one decision loop** | Read → retrieve rules → evidence → score → human decision → audit log. "No chat box: the product is built around a decision, not a conversation." |
| 5 | 3:10–3:50 | Core PM artifacts and decisions | **The hard choices** | Rejected AI approval and risk pricing. RICE ranked RAG low, and I kept it anyway because it carries the AI hypothesis. Bulk scan waits until accuracy is proven. |
| 6 | 3:50–6:30 | Prototype walkthrough | **Live demo** (script in [09](../04_Prototype_Readme_or_Link.md)) | ① POL200007 fails on content; ② evidence and confidence; ③ human decisions; ④ sign-off and report; ⑤ remove the key: Not Scored |
| 7a | 6:30–7:20 | Metrics and evidence | **Testing changed the product** | "My first prototype scored 100/100 when the AI failed. Later, 14 of 14 hid a skipped critical rule. Holdout found 16 of 16 with one false alarm, and one result changed between runs. That is promising, not proof." |
| 7b | 7:20–8:30 | Economics and launch risks | **People are the cost; time savings pay** | Inference is under 1% of run cost. **At US$150 an hour, time savings alone pay back US$360,000 in about 8–10 months; at only 20% time saved, about 26 months. Avoided remediation is upside.** Top blockers: critical recall, fabricated evidence, privacy approval. |
| 8 | 8:30–9:30 | Final recommendation | **Pilot, not scale** | "12 weeks, commercial property, 6–8 analysts, shadow mode first. Offline gates to enter; time and trust gates to scale; privacy or a 40% rejection rate stops it." |
| — | 9:30–10:00 | | Buffer / first question | |

## Slide requirements

- **Slide 1:** three numbers: 12,000 folders a year, 45 minutes a folder, US$1.35 million annual review cost, all marked as planning assumptions.
- **Slide 4:** the flow, plus what is in and out of the MVP.
- **Slide 7a:** the holdout table.
- **Slide 7b:** the payback table and three blockers.
- **Slide 8:** the gates on one line, ending on the recommendation.

## Likely questions

| Question | Answer |
|---|---|
| "Why not a simple rule script?" | I tested one. It found 8 of 30 planted defects and mistook misnamed documents for missing ones. It stays in the product for exact checks, but it cannot read content. |
| "Your data is synthetic. Why believe it?" | Don't rely on the accuracy figure. What the prototype shows is the workflow, the trust design and a repeatable test method. Real accuracy has to pass an offline gate first, and I expect it to be lower. |
| "16 of 16 sounds too good." | It may be. The data is tidy and small, and the confidence interval still allows recall near 79%. That is why I am asking for a pilot and not a rollout. |
| "What if the AI makes something up?" | Quotes are matched to the document, citations are limited to retrieved rules, and scans can't reach HIGH confidence. A person decides every finding. One fabricated finding in the audit blocks launch. |
| "Did RAG really help?" | Barely, at 22 rules: retrieving 10 is close to reading them all. Its value depends on a much larger real rulebook, and critical signature rules no longer depend on it. |
| "Is it safe to send policy data to an API?" | Not on a free tier, which is why the prototype uses synthetic data only. The pilot needs enterprise terms and privacy approval, or an in-house model. This is a launch blocker. |
| "Who owns it after the pilot?" | A rulebook owner in compliance at 0.5 FTE, already in the cost model. |
| "Will this replace analysts?" | No. Their time shifts from routine checks to judgment, and a person still decides each finding. |

## Before presenting

- [ ] Run one folder beforehand to confirm that the API key and quota work.
- [ ] Keep the screenshots ready in case the demo or network fails.
- [ ] Allow about 40 seconds for the live audit, and talk through the wait.
- [ ] Rehearse against the confirmed time limit.
- [ ] Close on the recommendation, not the demo.
