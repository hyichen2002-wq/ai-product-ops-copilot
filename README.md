# AI Product & Ops Copilot

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Local-first](https://img.shields.io/badge/Local--first-No%20API%20required-0F766E)](#api-boundary)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[中文说明](README_ZH.md)

AI Product & Ops Copilot is a local-first Streamlit dashboard for reviewing existing AI Assistant Q&A outputs, business feedback, and operations issues, then turning them into structured findings, ownership suggestions, and business-ready iteration actions.


## Project Boundary

This project is an offline evaluation and iteration tool for existing AI Assistant Q&A outputs. It is not the AI Assistant chatbot itself.

The first version does not implement RAG or Agent. It can evaluate outputs produced by an existing RAG or ReAct-style AI Assistant and help product or operations teams decide what to improve next.

## Demo Preview

The screenshots below show the main workflow of AI Product & Ops Copilot: from batch-level overview, bad case analysis, priority triage, to final report generation.

### Overview Dashboard

![Overview Dashboard](assets/screenshots/overview_dashboard.png)

The overview page summarizes the current feedback batch, including total cases, valid cases, duplicate cases, bad case count, high-priority cases, average user rating, and issue distribution.

### Bad Case Analysis

![Bad Case Analysis](assets/screenshots/bad_case_analysis.png)

The bad case analysis page identifies where existing AI Assistant answers may fail, such as missing steps, missing system entry, generic answers, failed human escalation, or hallucination risk.

### Priority Scoring

![Priority Scoring](assets/screenshots/priority_scoring.png)

The priority page converts detected issues into operational handling priorities, showing which issues should be handled first, which team should own them, and what next action is recommended.

### Report Generator

![Report Generator](assets/screenshots/report_generator.png)

The report generator creates a business-readable Markdown report for AI Assistant MVP review, HR/IT/Product iteration meetings, B2B operations reviews, or product operations retrospectives.

## Project Motivation

Many AI product and operations teams can collect feedback, but they still struggle to convert raw evaluation records into repeatable execution. This project demonstrates a practical interview-ready MVP: upload structured records, run a deterministic analysis pipeline, and generate an explainable report without depending on an external API.

## Target Business Scenarios

- AI Assistant MVP evaluation
- HR AI Assistant testing and policy QA review
- B2B operations issue triage
- Product and support feedback analysis
- E-commerce merchant operations review

## Quick Demo Flow

1. Launch the app locally.
2. Use the bundled mock dataset or upload a CSV, XLSX, or XLS file.
3. Start with Overview to explain the batch at a glance.
4. Inspect Bad Cases to show where the current assistant fails.
5. Review Priority to see owner and next-action recommendations.
6. Export the Markdown report for a meeting or retrospective.

## Key Features

- Local-first, rule-based analysis with no required external API
- CSV, XLSX, and XLS upload with fallback to bundled mock data
- Data cleaning with empty-row filtering and exact deduplication
- Rule-based issue classification for mixed Chinese and English feedback
- Bad case analysis for incomplete answers, missing steps, weak escalation, and hallucination risk
- Priority scoring with recommended owners, next actions, and owner action board summaries
- Markdown report generation for retrospectives and interview demos
- Download buttons for cleaned data, analyzed data, generated report, and Excel input template
- UTF-8-SIG CSV export for direct opening in Windows Excel

## System Flow

raw feedback -> cleaning -> classification -> bad case analysis -> priority scoring -> report generation

## Example Input

| raw_feedback | ai_answer | expected_behavior |
| --- | --- | --- |
| 我想开在职证明，在哪里申请？ | 请联系 HR 处理。 | Provide system entry, application steps, required materials, timeline, and support contact. |
| 物流节点一直没有更新，承运商说已经送达。 | 请等待系统同步。 | Check logistics node, carrier feedback, system status, and assign operations or data owner. |
| 我这种特殊情况能不能特殊审批年假？ | 可以申请。 | Escalate to human HR because this is a personal special case. |

## Example Output

| issue_category | bad_case_labels | priority_level | recommended_owner | next_action |
| --- | --- | --- | --- | --- |
| System Entry | missing_system_entry | High | IT Team | Add path, entry point, and link guidance |
| Data / Operation Exception | knowledge_gap \\| generic_answer | High | Operations Team | Update SOP and confirm process ownership |
| Human Escalation Needed | failed_human_escalation | High | Human Support | Add escalation rule and manual review boundary |

## Core Modules

| File | Role |
| --- | --- |
| src/cleaner.py | Normalizes text, removes empty rows, and performs exact deduplication before downstream analysis. |
| src/classifier.py | Assigns primary issue categories and secondary tags using deterministic business rules. |
| src/bad_case_analyzer.py | Evaluates existing AI answers for bad case patterns such as missing steps, weak escalation, and hallucination risk. |
| src/priority_scorer.py | Computes operational priority, recommended owner, and next action. |
| src/report_generator.py | Produces a business-facing Markdown summary for review meetings and iteration planning. |
| app.py | Streamlit UI entry point that handles upload, navigation, dashboard rendering, and downloads. |

## Input Schema

Supported input formats:

- CSV
- XLSX
- XLS

Required columns in the input template:

- case_id
- user_role
- source
- raw_feedback
- ai_answer
- user_rating
- expected_behavior
- business_impact
- frequency
- created_at

The repository includes a default dataset at [data/mock_feedback.csv](data/mock_feedback.csv) covering HR assistant testing, B2B operations, e-commerce merchant operations, and customer support scenarios.

## How To Run Locally

1. Create and activate a virtual environment if needed.
2. Install dependencies.
3. Start Streamlit.
4. Use the bundled mock dataset or upload your own CSV, XLSX, or XLS file.

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

No API key is required for the current version. Optional LLM-based classification and report enhancement are planned as future upgrades.

Downloaded CSV files use UTF-8-SIG encoding so Chinese characters display correctly when the files are opened directly in Microsoft Excel on Windows.

## How To Use The Demo

1. Start the app and keep the bundled dataset for demo mode, or upload your own structured file.
2. Use the left sidebar to upload data, check the data source, and download the standard Excel template.
3. Use Overview to summarize issue volume, source mix, and risk distribution.
4. Use Cleaning and Classification to explain how raw records are normalized and categorized.
5. Use Bad Cases to show where the current AI Assistant is failing.
6. Use Priority to show which team should act first and what they should do next.
7. Use Report to export a Markdown summary for review meetings.

## API Boundary

No API key is required for the current version.

The current release runs fully offline with deterministic rules. Optional LLM-based classification and report enhancement are future upgrade directions rather than a dependency of the MVP.


## How To Explain This Project In Interviews

- Position it as an evaluation layer for existing AI Assistant outputs rather than a chatbot demo.
- Explain that the first version intentionally uses deterministic rules so every classification and recommendation is inspectable.
- Walk through the pipeline from raw records to actionable output: cleaning, issue classification, bad case analysis, priority scoring, and report generation.
- Highlight that the app is useful even before a team invests in RAG, agents, or online experimentation infrastructure.
- Show how the UI helps non-technical stakeholders quickly see what failed, how serious it is, and which team should own the fix.
- One-line interview summary: Input existing AI Q&A results -> analyze issue categories and bad cases -> prioritize problems -> recommend owners and next actions.

## Limitations

- Classification and bad case detection are rule-based, so semantic recall is limited.
- Exact deduplication does not catch paraphrased duplicates.
- Charts and reports are best suited for small to medium batches.
- This release evaluates existing AI outputs; it does not generate or orchestrate answers in real time.

## Future Upgrade Path

- Semantic deduplication
- Optional LLM classification
- Report enhancement with optional LLM rewriting
- Evidence checking for RAG-based assistants
- Prompt version comparison
- LLM-as-Judge evaluation

## Open-Source Attribution

This project was originally derived from the open-source feedback analyzer template at https://github.com/kubraayvaz/feedback-analyzer.

The current repository has been substantially customized and extended into a new interview showcase focused on AI Assistant output evaluation, HR assistant review, B2B operations triage, support feedback analysis, and owner-based iteration planning.

## License

This project is available under the [MIT License](LICENSE).
