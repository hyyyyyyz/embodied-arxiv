// Maps the five matched_domain values to the CSS variables that hold their
// theme-aware accent color. Keeping this file tiny so /papers can import the
// same map in a follow-up refactor without dragging in homepage-specific code.

export const DOMAIN_TINT_VAR: Record<string, string> = {
  VLA: "--tint-vla-text",
  "World Model": "--tint-wm-text",
  WAM: "--accent-purple",
  VGGT: "--tint-vggt-text",
  Agent: "--tint-agent-text",
  Diffusion: "--tint-diff-text",
  "Multi-modal": "--tint-mm-text",
};

export function domainColor(domain: string): string {
  const v = DOMAIN_TINT_VAR[domain] ?? "--text-primary";
  return `var(${v})`;
}
