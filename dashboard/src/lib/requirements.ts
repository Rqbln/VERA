// The 12 measurable COMPL-AI requirements, grouped by EU AI Act principle.
// Mirrors COMPLAI_META in src/raip/dashboard/triage.py — keep in sync.

export interface RequirementMeta {
  id: string;
  name: string;
  principle: string;
}

export const REQUIREMENTS: RequirementMeta[] = [
  { id: "R01", name: "Robustness & predictability", principle: "Robustness & safety" },
  { id: "R02", name: "Cyber resilience", principle: "Robustness & safety" },
  { id: "R06", name: "Capabilities", principle: "Robustness & safety" },
  { id: "R03", name: "Training-data adequacy", principle: "Privacy & data governance" },
  { id: "R04", name: "Copyright compliance", principle: "Privacy & data governance" },
  { id: "R05", name: "Privacy protection", principle: "Privacy & data governance" },
  { id: "R07", name: "Calibration / interpretability", principle: "Transparency" },
  { id: "R08", name: "AI disclosure", principle: "Transparency" },
  { id: "R09", name: "Watermark / traceability", principle: "Transparency" },
  { id: "R10", name: "Representation bias", principle: "Fairness" },
  { id: "R11", name: "Fairness", principle: "Fairness" },
  { id: "R12", name: "Toxicity / harmful content", principle: "Fairness" },
];

export const PRINCIPLES = Array.from(new Set(REQUIREMENTS.map((r) => r.principle)));

// Inference-time defaults: requirements that work without a training dataset (R03–R05 need a corpus).
export const INFERENCE_REQUIREMENTS = REQUIREMENTS.filter(
  (r) => !["R03", "R04", "R05"].includes(r.id),
).map((r) => r.id);
