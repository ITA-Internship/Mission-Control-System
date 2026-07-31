/*
 * Single source of truth for the app-shell geometry.
 *
 * The sidebar width and top-bar height are referenced from three places
 * (Sidebar, TopBar, AppShell main). Encoding them once here keeps the sidebar,
 * the fixed top bar and the padded content area from drifting out of alignment
 * when the dimensions change. Values are expressed as Tailwind utility classes
 * (static strings, so the JIT compiler can see them) rather than inline pixels,
 * which also lets the offsets apply only from the `lg` breakpoint up — below it
 * the sidebar becomes an overlay drawer and the content spans full width.
 */

/* Expanded rail = 240px (w-60), collapsed icon rail = 64px (w-16). */
export function sidebarWidthClass(collapsed: boolean): string {
  return collapsed ? "lg:w-16" : "lg:w-60";
}

/* Left padding applied to the main content area on `lg` and up. */
export function contentOffsetClass(collapsed: boolean): string {
  return collapsed ? "lg:pl-16" : "lg:pl-60";
}

/* Left offset applied to the fixed top bar on `lg` and up. */
export function topBarOffsetClass(collapsed: boolean): string {
  return collapsed ? "lg:left-16" : "lg:left-60";
}
