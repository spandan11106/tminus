---
name: figure-handling
description: "Rules for using figures and charts from the book, slides or papers in tminus outputs: crop with crop_figure.py, view the image before using it, mark chart reads as approx. Use whenever a figure is cropped or a value is read off a chart."
user-invocable: false
---

# Figures and charts

Let `TM` be `${CLAUDE_PLUGIN_ROOT}/scripts/tm`.

1. **Crop**: `TM crop_figure <pdf> --printed <p> --offset <k> --caption "Fig. 5.3" --out figs/<name>.png`
   (or `--page <pdf page> --bbox x0,y0,x1,y1 --units frac`). Keep PNGs under 600 KB (lower `--dpi`).
2. **View the PNG with the Read tool before using it.** Check that it is the right figure, complete, not cut, and
   has no neighbouring text. Re-crop if not. Never insert a figure you have not looked at.
3. **Prefer tables to charts.** If the book tabulates a value, use the table and cite it.
4. **Reading a chart**: only after viewing the crop. Mark every read-off value with
   `\approxval{1.72}{Fig. 5.3, read at r/d = 0.1}` (Markdown: `1.72 (approx., read from Fig. 5.3 at r/d = 0.1)`).
   If a worked example in the book gives the value for the same inputs, use the book's value and cite it.
5. **Cite** every figure: source, printed page, figure number. Simple schematics may be drawn in TikZ instead.
6. **Copyright**: figures go only into the user's own outputs inside their course folder, never into the plugin repo.
