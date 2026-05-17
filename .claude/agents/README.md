# Dino Art — Agent Team

Eight focused subagents. Claude Code auto-routes work based on each agent's `description` field, or you can invoke explicitly with `@agent-name`.

| Agent | Stage | Model | Owns |
|---|---|---|---|
| [source-hunter](source-hunter.md) ⭐ v6 | Ref sourcing | haiku | `tools/source_paleoart.py`, `assets/staging/`, CC-license API queries |
| [license-auditor](license-auditor.md) ⭐ v6 | Legal gate | haiku | `tools/license_audit.py`, sidecar JSON quarantine flags |
| [caption-polisher](caption-polisher.md) ⭐ v6 | Caption authoring | sonnet | `<image>.txt` files, anatomy-only caption methodology |
| [ref-curator](ref-curator.md) | Reference layer | sonnet | `paleoart_refs.json`, `skeletal_refs.json`, `sref_sources.json`, `sref_urls.json`, `reference_images/`, `species_reference/` |
| [prompt-crafter](prompt-crafter.md) | Prompt assembly | sonnet | `generate_prompt.py`, parameter rules, A/B variants |
| [mj-logger](mj-logger.md) | MJ result tracking | sonnet | `prompts` / `results` / `prompt_parameters` / `ab_*` tables |
| [printify-publisher](printify-publisher.md) | Product creation | sonnet | `drops/`, `printify_api.py`, sidecar ledgers |
| [site-custodian](site-custodian.md) | Frontend gallery | sonnet | `site/` Astro project |

## v6 Research Pipeline (cost-optimized)

The three ⭐ agents form the new sourcing pipeline, designed to minimize Claude API usage:

```
source-hunter (haiku)    → calls tools/source_paleoart.py → assets/staging/<species>/<category>/
caption-polisher (sonnet) ← reads Ollama drafts from tools/caption_draft.py → writes <stem>.txt
license-auditor (haiku)   → calls tools/license_audit.py → blocks or approves before training_refs/
```

Deterministic work (API queries, downloads, hashing) runs in Python with zero AI cost. Local Ollama on the 2016 MBP or M1 mini drafts captions. Claude only does judgment work — polishing captions, picking candidates, strategic decisions. Estimated 5-10x cost reduction vs running everything through Sonnet conversations.

## Why this split

Each stage has a different *failure mode* — anatomy errors at the ref layer, weighting bugs at the prompt layer, missing metadata at the logging layer, pricing bugs at the publish layer, layout bugs at the site layer. Keeping them separate means a problem in one stage doesn't pull in context from the other four.

## How they hand off

```
source-hunter → caption-polisher → license-auditor → ref-curator → prompt-crafter → (you generate in MJ or Flux) → mj-logger → printify-publisher → site-custodian
```

Each handoff is a file or a DB row, not a conversation. If an agent finds work that belongs to a neighbor, it flags and stops rather than reaching across.

## Adding a sixth agent

Only add one when a sustained class of work doesn't fit any of the five. Each new agent dilutes the routing signal, so the bar should be high.
