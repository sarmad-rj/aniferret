# Rule: Airbnb React/JSX Style Guide

All frontend files in `frontend/src/` must strictly adhere to the Airbnb React/JSX standards:

1. **Naming Conventions:**
   - PascalCase for JSX component filenames and identifiers (`DossierCard.jsx`, `HierarchyTree.jsx`).
   - camelCase for props, helper functions, and state instances (`isLoading`, `currentEpisode`).
2. **Props & Booleans:**
   - Omit explicit `true` on boolean attributes (`<Card isFeatured />` instead of `<Card isFeatured={true} />`).
   - Wrap multi-line JSX props in parentheses with standard 2-space indentation.
3. **Component Architecture:**
   - Use functional components exclusively (no React class components).
   - Order hook declarations systematically: `useState` $\to$ `useRef` $\to$ custom hooks $\to$ `useEffect` $\to$ event handler functions $\to$ `return (...)`.
4. **Self-Closing Elements:**
   - Any component without children must be self-closing (`<img src="..." alt="..." />`, `<Avatar />`).
