# RAIP governance policy (MVP4 gaas).
#
# Mirrors raip.governance.policy.builtin_decision so the OPA path and the in-process fallback agree.
# Query:  POST /v1/data/raip/governance/decision   with {"input": {...}}
# Input:  {model, mode, kill_switch, trust_score, signals}
# Result: {decision: "allow"|"flag"|"deny", reasons: [string], source: "opa"}
package raip.governance

import rego.v1

default block_below := 0.30
default warn_below := 0.60

# --- reasons ----------------------------------------------------------------
reasons contains "kill-switch engaged" if input.kill_switch

reasons contains msg if {
	is_number(input.trust_score)
	input.trust_score < block_below
	msg := sprintf("trust %.2f < block %.2f", [input.trust_score, block_below])
}

reasons contains msg if {
	is_number(input.trust_score)
	input.trust_score >= block_below
	input.trust_score < warn_below
	msg := sprintf("trust %.2f < warn %.2f", [input.trust_score, warn_below])
}

# --- would-deny (before mode gating) ---------------------------------------
would_deny if input.kill_switch

would_deny if {
	is_number(input.trust_score)
	input.trust_score < block_below
}

would_flag if {
	is_number(input.trust_score)
	input.trust_score < warn_below
}

# --- decision: only enforcement mode actually blocks -----------------------
decision := "deny" if {
	input.mode == "enforcement"
	would_deny
}

decision := "flag" if {
	not (input.mode == "enforcement"; would_deny)
	would_deny
}

decision := "flag" if {
	not would_deny
	would_flag
}

default decision := "allow"

result := {
	"decision": decision,
	"reasons": [r | some r in reasons],
	"source": "opa",
}
