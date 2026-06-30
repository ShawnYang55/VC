---
name: notion-writer
description: Write, rewrite, or update Notion product documents, PRDs, strategy notes, design principles, and structured documentation from user notes or existing context. Use when the user asks Codex to publish content into Notion, refresh an existing Notion page, replace page blocks, create/update product docs, or turn messy discussion into a polished Notion-ready document.
---

# Notion Writer

## Overview

Use this skill to turn user context into polished Notion pages and to update existing Notion documents safely. Prefer structured Notion blocks over dumping markdown text when the user wants a durable product, strategy, or operating document.

## Workflow

1. Clarify the target Notion page or database.
   - Ask for a URL/page ID only if it is not already present in the thread or discoverable from prior local context.
   - Identify whether the user wants a new page, an append, or a full replacement.
   - For destructive replacements, confirm intent before archiving existing blocks unless the user clearly asked to refresh/replace the document.

2. Gather context.
   - Use the user's notes, linked pages, attached files, existing drafts, and any explicitly provided prior context.
   - Search local workspace files only when the user asks to reuse local context or when the current task clearly depends on local drafts.
   - Preserve useful product language, version numbers, page titles, and conceptual decisions.

3. Compose the document before writing.
   - Produce a clean outline with H1/H2/H3 sections, bullets, numbered flows, callouts, quotes, dividers, and code blocks where appropriate.
   - For PRDs, include goal, users, flows, scope, requirements, UX notes, metrics, risks, and open questions.
   - For design principles, separate product philosophy from implementation detail.

4. Write through Notion.
   - Prefer available Notion connector tools when they can perform the requested write.
   - For bulk page replacement or precise block construction, adapt `scripts/notion_update_template.py`.
   - Use batched appends of at most 100 blocks.
   - Split rich text chunks below Notion limits.
   - Retry transient failures and handle rate limits.

5. Verify.
   - Fetch the page after writing and report the Notion URL.
   - Summarize what changed: title, page(s), update mode, and major sections.
   - Mention any skipped blocks, archived-block issues, or permission failures.

## Notion API Pattern

Use the API pattern from `scripts/notion_update_template.py` when a connector is unavailable or when deterministic full-page replacement is needed:

- Read the Notion token from `NOTION_TOKEN` first, then from a user-provided local token file when available.
- Patch page properties such as title, category, and icon.
- Fetch existing page children with pagination.
- Archive existing children only after replacement intent is clear.
- Append new blocks in batches of 100.
- Return the final page URL.

Do not print or store secrets in generated output. Do not hard-code tokens into a skill, script, or final answer.
