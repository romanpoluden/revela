# Final UI Design Direction

Parent issue: #196  
Child issue: #208

## Purpose

This document defines the final visual and UX direction for the Revela Streamlit UI before implementation.

The goal is to guide later UI polish work without changing model behavior, inference logic, taxonomy, model registry, training code, model artifacts, or prompt-builder logic.

## Product Positioning

Revela should be presented as an educational dermatology AI training aid.

The UI should support structured image review for learning. It should help learners understand model outputs, confidence, uncertainty, limitations, and safe next steps for educational reflection.

The product must not be framed as a diagnostic assistant, clinical decision-support tool, patient self-diagnosis app, or treatment recommendation system.

## Visual Direction

The final UI should feel like a premium medical education dashboard with a warm dermatology and skin-tone inspired palette.

The interface should feel:

- credible;
- calm;
- premium;
- educational;
- medically careful;
- appropriate for a final demo.

The interface should not feel:

- like a beauty clinic;
- like a patient self-diagnosis app;
- overly decorative;
- cold hospital-blue only;
- cluttered or experimental.

## Color Palette Direction

The color system should use warm clinical neutrals with subtle dermatology-inspired accents.

Recommended direction:

- Background: warm ivory, soft beige, or very light sand.
- Main cards: white or near-white for readability.
- Primary accent: muted terracotta, clay, or warm skin-tone brown.
- Secondary accent: taupe, sand, or soft beige-gray.
- Safety or caution emphasis: muted amber or warm brown.
- Main text: charcoal or dark brown-gray.
- Borders: light beige-gray or warm neutral gray.

Avoid colors that make the app feel cosmetic, decorative, or patient-facing, such as strong pink, beauty-brand peach, neon tones, or heavy gradient styling.

## Card Styling Direction

Cards should feel like structured learning modules.

Use cards to separate:

- product framing;
- mode selection;
- upload instructions;
- learner context;
- clinical-photo results;
- dermoscopic-image results;
- uncertainty and confidence explanation;
- limitations and safety notes;
- prompt export.

Card styling should prioritize:

- consistent padding;
- subtle borders;
- soft shadows;
- rounded corners;
- clear section titles;
- short helper text;
- visible safety callouts.

The UI should avoid dense blocks of text and should not hide critical warnings.

## Typography and Hierarchy Direction

The typography should make the app easy to understand during screen sharing.

Recommended hierarchy:

- Page title: clear and confident.
- Subtitle: short educational scope statement.
- Section headings: action-oriented and easy to scan.
- Helper text: plain English and concise.
- Result labels: clear, structured, and not overly clinical.
- Safety notes: visually visible and easy to find.

The hierarchy should guide the user through the flow without requiring long spoken explanation.

## Layout and Spacing Direction

The layout should feel calm, structured, and demo-ready.

Use:

- generous vertical spacing between major sections;
- consistent spacing inside cards;
- clear separation between clinical and dermoscopic flows;
- clear separation between result output and safety limitations;
- visible reset or start-over action placement;
- simple narrow-screen behavior where practical.

Avoid visual clutter, excessive columns, hidden warnings, or crowded result areas.

## Safety Copy Tone

The copy should be educational, careful, and transparent.

Recommended wording:

- educational dermatology AI training aid;
- structured image review for learning;
- model output, not diagnosis;
- confidence is model confidence, not clinical certainty;
- qualified review is required for real clinical decisions;
- prompt export is manual copy to the learner's preferred LLM;
- the app does not call ChatGPT or Claude directly;
- uploaded images are not sent to external LLMs by the app.

Avoid wording such as:

- diagnostic assistant;
- clinical decision support;
- confirmed;
- detected;
- safe lesion;
- treatment recommendation;
- clinically validated;
- patient-use ready.

## Result Screen Direction

The result screen should make the model output easier to scan while preserving safety.

Result areas should:

- clearly show the top model output;
- explain confidence without implying certainty;
- show uncertainty in plain language;
- keep top-k predictions readable;
- keep limitations visible;
- clearly separate clinical and dermoscopic results if both are shown;
- avoid framing "Other non-cancer / indeterminate lesion" as safe.

## Prompt Export Direction

The prompt export panel should feel useful and safe.

It should make clear that:

- the app generates a prompt for manual copy;
- the app does not call ChatGPT or Claude directly;
- uploaded images are not sent to external LLMs by the app;
- the exported prompt must preserve educational-only safety framing;
- the LLM should help explain reasoning, not diagnose or recommend treatment.

## Implementation Guidance for Later UI Polish

Later implementation work should use this document as design guidance only.

Implementation should stay within the scope of UI polish and should not change:

- model behavior;
- inference logic;
- taxonomy;
- model registry;
- training code;
- model artifacts;
- prompt-builder logic, unless a change is strictly UI copy display and separately justified.

## Acceptance Criteria Mapping

This document satisfies #208 by:

- documenting the final UI direction;
- connecting the visual direction to Revela's educational dermatology scope;
- defining a clear safety-copy tone;
- avoiding diagnostic, treatment, clinical-readiness, and patient-use claims;
- preparing a safe reference for later UI polish work under #196.
