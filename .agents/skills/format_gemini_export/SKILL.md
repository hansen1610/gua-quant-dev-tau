---
name: Format Gemini Export
description: Converts a raw Gemini markdown export into a clean, viewer-friendly guide.
---

# Skill: Format Gemini Export

This skill provides instructions on how to process raw conversation exports from Gemini and transform them into easy-to-read, structured documentation or technical guides.

## Context
When a user exports a conversation from Gemini, the resulting markdown file often contains noise such as navigation menus, UI elements, and irrelevant context. This skill helps extract the core knowledge into a clean format.

## Execution Steps

1. **Information Extraction**:
   - Read the raw Gemini markdown file provided by the user.
   - Strip out extraneous UI text, such as sidebar navigation links, "Percakapan", profile images, and embedded iframe tags.
   - Identify the user's main prompt and the core technical solutions provided by the AI.

2. **Formatting & Restructuring**:
   - Create an appropriate main heading (`# Guide: [Topic]`).
   - Add a brief introductory paragraph summarizing the context or problem.
   - Organize the solutions into distinct sections using `##` subheadings.
   - Use bullet points (`-`) or numbered lists for actionable steps.
   - Use formatting (like **bolding**) to emphasize settings, file names, or key terms.
   - Utilize GitHub-style alerts (e.g., `> [!NOTE]`, `> [!IMPORTANT]`, `> [!WARNING]`) to highlight critical tips, edge cases, or warnings.

3. **Output Generation**:
   - Save the cleaned and formatted content into a new `.md` file with a descriptive, professional name.
   - Return the path to the user and optionally present a preview of the clean file.

4. **Follow-up Prompt (Validation)**:
   - After successfully delivering the formatted file, ask the user if they would like to validate the factual accuracy of the document using the **Generate Validation Report** skill.
   - *Note:* Make it clear that this is optional, as the user might only want the formatting. (Example: "Apakah Anda ingin saya memvalidasi poin-poin teknis di file ini menggunakan skill Generate Validation Report?").

## Example Result
A cluttered export containing links like `[Mengatasi CPU 100% Antigravity](/app)` should be transformed into:
```markdown
# Guide: Mengatasi CPU 100% pada Antigravity
...
## 1. Downgrade ke Versi Stabil...
```
