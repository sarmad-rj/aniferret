# Rule: AniFerret UI Design System & Dynamic CSS Variable Architecture

All frontend components in `frontend/src/` must strictly adhere to the AniFerret Visual Identity and CSS Variable architecture defined below.

---

## 1. Palette & CSS Variable Tokens

The primary theme for AniFerret is **Light Mode First**, driven by the mascot identity: **Deep Navy + Sky Blue + Sakura Pink + Warm Cream + Ferret Brown**.

All colors are declared in `frontend/src/index.css` via `:root` CSS variables. **Zero raw hex codes may be hardcoded inside React JSX components.**

```css
:root {
  /* Brand Core */
  --primary: #111A38;          /* Deep Navy (Navbar, headings, primary buttons) */
  --primary-light: #202A4A;    /* Soft Navy (Hover states, elevated elements) */

  /* Surfaces & Backgrounds */
  --background: #EAF7FB;       /* Mist Blue (Main website canvas) */
  --surface: #FFFFFF;          /* Pure White (Cards, input backgrounds) */
  --surface-warm: #FFF5E6;     /* Warm Cream (Featured sections, mascot accents) */

  /* Accents & Progress */
  --sky: #8CCFE5;              /* Sky Blue (Episode progress bars, highlights) */
  --pink: #F3A6B8;             /* Sakura Pink (Spoiler locks, active indicators) */
  --pink-light: #FAD5DE;       /* Soft Pink (Selected item backgrounds, soft tags) */
  --ferret: #B97855;           /* Ferret Brown (Mascot accents, secondary badges) */

  /* Typography & Borders */
  --text: #18213D;             /* Deep Navy (Primary body text) */
  --text-muted: #65758B;       /* Blue Gray (Metadata, episode citations) */
  --border: #D5E4EA;           /* Soft Blue Gray (Dividers, card borders) */
}
```

---

## 2. The 60-25-10-5 Visual Balance Rule

To maintain a sophisticated, clean UI:
- **60% Dominance**: Mist Blue Canvas (`--background`), White Cards (`--surface`), and Warm Cream (`--surface-warm`).
- **25% Structure**: Deep Navy (`--primary`) for headers, navigation, and primary typography.
- **10% Progress**: Sky Blue (`--sky`) for watch progress bars, episode counters, and relation node lines.
- **5% Accent**: Sakura Pink (`--pink`) and Ferret Brown (`--ferret`) reserved strictly for spoiler locks, active badges, and mascot callouts.

---

## 3. Progress Visualization & Spoiler Status System

### Progress Bars (Episode 1 $\to$ 12)
- **Completed Episodes**: `--sky` (`#8CCFE5`)
- **Current Active Episode**: `--pink` (`#F3A6B8`)
- **Unwatched Episodes**: `--border` (`#D5E4EA`)

### Spoiler Shield Badge
- **Locked State**: Subtle `--pink-light` (`#FAD5DE`) background with `--pink` (`#F3A6B8`) lock icon and `--primary` text:
  > 🔒 *Information available up to Episode 12*

---

## 4. Theme Customizer Architecture (Easy Theme Switching)

To allow instant live theme customization (e.g. on a dev route `/admin/theme`):
1. **Component Binding Requirement**: Every component uses CSS variable references (e.g., `color: var(--text)`, `background: var(--surface)`).
2. **Dynamic Live Theme Swapping**: Updating `document.documentElement.style.setProperty('--primary', newColor)` instantly updates the entire website's appearance without code modification or re-compilation.
