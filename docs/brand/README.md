# transkribierBAR brand

The name is written **transkribierBAR**. Where it is set next to the logo,
"BAR" takes the accent colour, as in the wordmark.

## Files

| File | Use |
| --- | --- |
| `docs/brand/transkribierbar-logo-light.svg` | Mark and wordmark for light backgrounds, transparent. The sign-in page of the deployment shows a copy |
| `docs/brand/transkribierbar-logo-dark.svg` | Mark and wordmark with a glow, for dark backgrounds, transparent |
| `frontend/public/logo-mark.svg` | Mark alone. The app header and the Handbuch masthead draw it next to the name set as text |
| `frontend/public/favicon.svg`, `favicon.ico` | Browser icons for the app and the Handbuch |

The wordmark in the SVG files is converted to outlines, so they need no font.

## Colours

The mark's gradient runs `#FF5A1C` → `#FF6F1F` → `#FFA531` → `#FFBF45`.
The accent for text is a darker orange so it reaches 4.5:1: `#C2410C` on light
backgrounds and `#FB923C` on dark ones (`--accent` in
`frontend/src/help/render/guide.css`, `text-orange-400` in the app header).
