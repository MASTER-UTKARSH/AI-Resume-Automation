---
name: Clyde
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1b1b1b'
  surface-container: '#1f1f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353535'
  on-surface: '#e2e2e2'
  on-surface-variant: '#cfc4c5'
  inverse-surface: '#e2e2e2'
  inverse-on-surface: '#303030'
  outline: '#988e90'
  outline-variant: '#4c4546'
  surface-tint: '#c6c6c6'
  primary: '#c6c6c6'
  on-primary: '#303030'
  primary-container: '#000000'
  on-primary-container: '#757575'
  inverse-primary: '#5e5e5e'
  secondary: '#c6c7c5'
  on-secondary: '#2f3130'
  secondary-container: '#454746'
  on-secondary-container: '#b4b5b4'
  tertiary: '#c6c6c6'
  on-tertiary: '#303030'
  tertiary-container: '#000000'
  on-tertiary-container: '#757575'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e2e2e2'
  primary-fixed-dim: '#c6c6c6'
  on-primary-fixed: '#1b1b1b'
  on-primary-fixed-variant: '#474747'
  secondary-fixed: '#e2e3e1'
  secondary-fixed-dim: '#c6c7c5'
  on-secondary-fixed: '#1a1c1b'
  on-secondary-fixed-variant: '#454746'
  tertiary-fixed: '#e2e2e2'
  tertiary-fixed-dim: '#c6c6c6'
  on-tertiary-fixed: '#1b1b1b'
  on-tertiary-fixed-variant: '#474747'
  background: '#131313'
  on-background: '#e2e2e2'
  surface-variant: '#353535'
  obsidian: '#000000'
  bone: '#f6f6f4'
  slate: '#7d7d7d'
  paper: '#ffffff'
  char: '#1a1a1a'
  solstice-gradient: 'linear-gradient(90deg, #feed7a 0%, #ff8400 48.96%, #df91f7 100%)'
typography:
  display:
    fontFamily: Recoleta
    fontSize: 125px
    fontWeight: '400'
    lineHeight: '1.0'
    letterSpacing: -3.75px
  headline-lg:
    fontFamily: Recoleta
    fontSize: 80px
    fontWeight: '400'
    lineHeight: '1.0'
    letterSpacing: -2.4px
  headline-lg-mobile:
    fontFamily: Recoleta
    fontSize: 48px
    fontWeight: '400'
    lineHeight: '1.1'
    letterSpacing: -1.5px
  heading:
    fontFamily: Recoleta
    fontSize: 61px
    fontWeight: '400'
    lineHeight: '1.1'
    letterSpacing: -1.22px
  heading-sm:
    fontFamily: Recoleta
    fontSize: 47px
    fontWeight: '400'
    lineHeight: '1.1'
    letterSpacing: -0.94px
  subheading:
    fontFamily: Recoleta
    fontSize: 36px
    fontWeight: '400'
    lineHeight: '1.1'
    letterSpacing: -0.36px
  body-lg:
    fontFamily: Oldschool Grotesk
    fontSize: 21px
    fontWeight: '400'
    lineHeight: '1.3'
    letterSpacing: -0.42px
  body:
    fontFamily: Oldschool Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: -0.16px
  label:
    fontFamily: Oldschool Grotesk
    fontSize: 15px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: 0.15px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 20px
  sm: 24px
  md: 44px
  lg: 64px
  xl: 92px
  xxl: 144px
  max-width: 1200px
  section-gap: 80px
---

## Brand & Style

The design system for this AI career assistant is rooted in a **Dark Editorial** aesthetic, drawing inspiration from high-end fashion monographs and gallery catalogs. The brand personality is quiet, sophisticated, and authoritative—shifting the focus away from typical "tech" tropes toward a timeless, print-inspired layout.

The visual narrative is defined by:
- **Achromatic Dominance:** A strictly limited palette that prioritizes contrast and legibility over decorative color.
- **Sculptural Typography:** Aggressive, tight leading and negative letter-spacing in serif headlines to create a "sculpted" text effect.
- **Technical Precision:** The use of hairline borders and pill-shaped UI elements provides a sharp, engineered contrast to the fluid, organic 3D shapes that serve as the brand's singular visual accent.
- **Minimalist Restraint:** Whitespace is treated as a structural element, with an explicit rejection of shadows and traditional depth metaphors in favor of tonal layering.

## Colors

The color strategy is 99% achromatic. **Obsidian** serves as the primary canvas, creating a deep, immersive environment. **Bone** is used for primary text and hairline borders to maintain a warm, sophisticated legibility that is softer than pure white.

**Solstice Gradient** is the only chromatic element in the design system. It must be used exclusively for:
1. Abstract 3D organic shapes.
2. High-impact, small-scale product accents (e.g., a notification dot or a subtle status indicator).

Functional state changes (hover, active) should be handled through **tonal inversion** (e.g., swapping Obsidian and Bone) rather than introducing new hues.

## Typography

This system uses a sharp distinction between the luxurious, high-contrast serif **Recoleta** (for all editorial headings) and the technical **Oldschool Grotesk** (for UI and body text).

**Key Implementation Rules:**
- **Aggressive Tightening:** As font size increases, letter-spacing must become more negative to maintain the "compact" magazine look.
- **Vertical Rhythm:** Display and Large Headings use a 1.0 line-height. Ensure adequate paragraph spacing (padding-bottom) to prevent overlap.
- **Mobile Adaptation:** For screens smaller than 768px, scale display type significantly (see `headline-lg-mobile`) while maintaining the serif family.
- **UI/Labels:** Use the Grotesk font for navigation, buttons, and form labels to ensure a technical, functional feel amidst the editorial headings.

## Layout & Spacing

The layout philosophy follows a **Fixed Grid** model on desktop (max-width 1200px) that transitions to a fluid model on smaller devices. The spacing rhythm is generous, emphasizing vertical breathing room to mimic a physical magazine page.

- **Grid:** Use a 12-column grid for desktop with 24px gutters.
- **Margins:** Page margins should be at least 24px on mobile and 64px on desktop.
- **Verticality:** Use the `xxl` (144px) and `xl` (92px) tokens for section spacing to create distinct thematic breaks. 
- **Density:** Card and container internal padding should remain consistent at 24px (`sm`) to maintain a compact, "engineered" look for technical data.

## Elevation & Depth

This design system explicitly **rejects the use of shadows**. Hierarchy and depth are achieved through two specific techniques:

1.  **Tonal Layering:**
    - **Level 0:** The base canvas is always #000000 (Obsidian).
    - **Level 1:** Secondary surfaces or featured sections use #f6f6f4 (Bone).
    - **Level 2:** Interior panels or active tabs use #7d7d7d (Slate).
    - **Level 3:** The highest contrast elements, like inner product cards, use #ffffff (Paper).

2.  **Hairline Borders:** Use 1px borders to define shapes. On dark backgrounds, use #f6f6f4 (Bone) or #1a1a1a (Char) for subtle definition. On light backgrounds, use #1a1a1a (Char).

## Shapes

The shape language is a deliberate mix of sharp technicality and extreme softness. 

- **Pill Shapes:** All interactive triggers (Buttons, Chips, Tags, Tabs) must use a 100px border radius to create a distinct "pill" silhouette.
- **Card Geometry:** Containers and product cards use a 16px radius to feel modern but structured.
- **Small Elements:** Functional inputs use a tight 4px radius to distinguish them from pill-shaped buttons.
- **Decorative:** 3D assets should remain fluid and organic, providing a visual foil to the geometric precision of the UI.

## Components

### Buttons
- **Style:** Pill-shaped (100px radius).
- **Primary:** Obsidian fill with Bone text on light surfaces; Bone fill with Obsidian text on dark surfaces.
- **Secondary:** Hairline border (1px) with transparent fill.
- **Sizing:** Generous horizontal padding to emphasize the pill shape.

### Input Fields
- **Style:** 4px border radius with a 1px hairline border.
- **Background:** Transparent or Char (#1a1a1a) for subtle depth.
- **Text:** Oldschool Grotesk, 16px.

### Cards
- **Style:** 16px border radius with a 1px hairline border (#1a1a1a on light; #f6f6f4 on dark).
- **Shadows:** None. Depth is communicated via the background fill (Paper or Bone).

### Chips & Tags
- **Style:** Small pill shapes (100px radius).
- **Text:** 15px Body SM (Labels).
- **Colors:** Use Slate (#7d7d7d) for background or simple hairline outlines.

### Lists & Dividers
- **Dividers:** 1px hairline horizontal or vertical lines. In the "Stats Feature Bar," use vertical 1px Bone dividers to separate content blocks.

### 3D Abstract Blobs
- These are treated as components themselves. They should be placed to overlap section transitions or act as focal points in hero sections, always featuring the Solstice Gradient.