# Writing style for questions and solutions (all outputs)

The student reads these under time pressure. Give every idea its own line and leave white space. Dense is not
efficient. The user asked for this explicitly after reviewing the first real-course packs.

## Problems
- Open with one or two plain sentences saying what the situation is.
- Put the data in `tmgiven`, one quantity per item with its unit (Markdown: a bullet list under **Given**).
- Put what is asked in `tmfind`, numbered (i), (ii) (Markdown: a numbered list under **Find**).

## Solutions
- Use `tmsolution`. Each item is one step: a short sentence saying what the step does and why (which formula,
  which convention, which case), then **one** displayed equation with the numbers substituted and the result.
- Never chain several computations in one sentence or one line, as in "P = ..., so I = ..., so E = ...".
  Split them into separate steps.
- State decisions as their own step: "Delta connection, so the phase voltage equals the line voltage".
- Close with `\tmans{...}`: final values with units, then one short line of interpretation if useful.
- A note about the book's rounding or a convention goes in a separate short paragraph after the answer.

## Mock questions
- Use `tmquestion{n}{marks}` for each question. Sub-parts go in `tmparts`, one per line. Multiple-choice options
  go in `tmoptions`, one per line, never run together in a sentence.
- Leave visible space between questions.

## Recipes and traps
- Recipe steps: one action each, at most two lines. Put the decision first ("If Delta: ...; if Y: ...").
- Traps: a bold title, then one or two sentences.

## Markdown mode
Use the same structure: headings for each example, **Given**, **Find** and **Solution** labels, numbered steps
with `$$ ... $$` displays on their own lines, and a blank line between steps.
