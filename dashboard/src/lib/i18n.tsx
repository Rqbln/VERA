"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

// Lightweight bilingual layer (FR/EN). Technical acronyms (EU AI Act, COMPL-AI, LLM, RBAC, HITL,
// CI, Trust Factor, GaaS) are intentionally kept identical in both locales. Components opt in via
// useT(); any component that does not is simply rendered in its source language.

export type Locale = "en" | "fr";

const EN = {
  "app.title": "RAIP Control Room",
  "nav.home": "Home",
  "nav.launch": "Launch evaluation",
  "nav.runs": "Runs",
  "nav.governance": "Governance",
  "nav.compliance": "Compliance",
  "nav.cyber": "Cyber",
  "nav.ds": "Data Science",
  "nav.guided": "Guided mode · no login",
  "nav.signout": "Sign out",

  "home.welcome": "Welcome to RAIP",
  "home.intro":
    "RAIP checks whether an AI model meets the EU AI Act requirements. Launch an evaluation on a connected model and read a clear summary — no code, no login.",
  "home.kpi.models": "Connected models",
  "home.kpi.connected": "connected",
  "home.kpi.completed": "Completed runs",
  "home.kpi.running": "In progress",
  "home.action.launch.title": "Launch an evaluation",
  "home.action.launch.body":
    "Pick a connected model and check it against EU AI Act requirements. Guided, no setup.",
  "home.action.runs.title": "View runs & scores",
  "home.action.runs.body":
    "A summary table of every evaluation: status, model, and the R01–R12 compliance picture.",
  "home.action.compliance.title": "Compliance control room",
  "home.action.compliance.body":
    "The full triage view: failed/fallback/uncovered requirements first, with rationale and CIs.",
  "home.action.governance.title": "Governance runtime",
  "home.action.governance.body":
    "Continuous oversight: live Trust Factor, per-model mode, incidents, and the kill-switch.",
  "home.action.cta": "Open",
  "home.bands":
    "Each requirement gets a band — green (compliant), amber (watch), red (action needed). No hard pass/fail: a human reviews the trade-offs.",

  "gov.title": "Governance runtime",
  "gov.subtitle":
    "Continuous, auditable oversight of governed inference (MVP4). Modes: shadow observes, advisory alerts, enforcement blocks.",
  "gov.proxy": "Proxy",
  "gov.bus": "Event bus",
  "gov.policy": "Policy engine",
  "gov.audit": "Audit / SIEM",
  "gov.mode": "Mode",
  "gov.trust": "Trust Factor",
  "gov.incidents": "Incidents",
  "gov.killswitch": "Kill-switch",
  "gov.killswitch.on": "engaged — new runs blocked",
  "gov.killswitch.off": "off — evaluations can run",
  "gov.engage": "Engage",
  "gov.reenable": "Re-enable",
  "gov.no_incidents": "No incidents recorded.",

  "common.status": "Status",
  "common.model": "Model",
  "common.loading": "Loading…",
  "lang.toggle": "FR",
} as const;

type Key = keyof typeof EN;

const FR: Record<Key, string> = {
  "app.title": "RAIP — Salle de pilotage",
  "nav.home": "Accueil",
  "nav.launch": "Lancer une évaluation",
  "nav.runs": "Évaluations",
  "nav.governance": "Gouvernance",
  "nav.compliance": "Conformité",
  "nav.cyber": "Cyber",
  "nav.ds": "Data Science",
  "nav.guided": "Mode guidé · sans connexion",
  "nav.signout": "Se déconnecter",

  "home.welcome": "Bienvenue dans RAIP",
  "home.intro":
    "RAIP vérifie si un modèle d’IA respecte les exigences de l’EU AI Act. Lancez une évaluation sur un modèle connecté et lisez un résumé clair — sans code, sans connexion.",
  "home.kpi.models": "Modèles connectés",
  "home.kpi.connected": "connectés",
  "home.kpi.completed": "Évaluations terminées",
  "home.kpi.running": "En cours",
  "home.action.launch.title": "Lancer une évaluation",
  "home.action.launch.body":
    "Choisissez un modèle connecté et confrontez-le aux exigences de l’EU AI Act. Guidé, sans configuration.",
  "home.action.runs.title": "Voir les évaluations & scores",
  "home.action.runs.body":
    "Un tableau récapitulatif de chaque évaluation : statut, modèle et conformité R01–R12.",
  "home.action.compliance.title": "Salle de pilotage conformité",
  "home.action.compliance.body":
    "La vue de triage complète : exigences en échec/repli/non couvertes en premier, avec justificatifs et IC.",
  "home.action.governance.title": "Runtime de gouvernance",
  "home.action.governance.body":
    "Supervision continue : Trust Factor en direct, mode par modèle, incidents et kill-switch.",
  "home.action.cta": "Ouvrir",
  "home.bands":
    "Chaque exigence reçoit une pastille — vert (conforme), ambre (à surveiller), rouge (action requise). Pas de seuil binaire : un humain arbitre.",

  "gov.title": "Runtime de gouvernance",
  "gov.subtitle":
    "Supervision continue et auditable de l’inférence gouvernée (MVP4). Modes : shadow observe, advisory alerte, enforcement bloque.",
  "gov.proxy": "Proxy",
  "gov.bus": "Bus d’événements",
  "gov.policy": "Moteur de politiques",
  "gov.audit": "Audit / SIEM",
  "gov.mode": "Mode",
  "gov.trust": "Trust Factor",
  "gov.incidents": "Incidents",
  "gov.killswitch": "Kill-switch",
  "gov.killswitch.on": "activé — nouveaux runs bloqués",
  "gov.killswitch.off": "inactif — les évaluations peuvent tourner",
  "gov.engage": "Activer",
  "gov.reenable": "Réactiver",
  "gov.no_incidents": "Aucun incident enregistré.",

  "common.status": "Statut",
  "common.model": "Modèle",
  "common.loading": "Chargement…",
  "lang.toggle": "EN",
};

const DICT: Record<Locale, Record<Key, string>> = { en: EN, fr: FR };

interface I18nValue {
  locale: Locale;
  setLocale: (l: Locale) => void;
  toggle: () => void;
  t: (key: Key | string) => string;
}

const I18nContext = createContext<I18nValue | null>(null);

function defaultLocale(): Locale {
  const env = (process.env.NEXT_PUBLIC_DEFAULT_LOCALE as Locale) || "en";
  return env === "fr" ? "fr" : "en";
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(defaultLocale());

  useEffect(() => {
    const saved = typeof window !== "undefined" ? (localStorage.getItem("raip-locale") as Locale | null) : null;
    if (saved === "fr" || saved === "en") setLocaleState(saved);
  }, []);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    if (typeof window !== "undefined") localStorage.setItem("raip-locale", l);
  }, []);

  const toggle = useCallback(() => setLocale(locale === "en" ? "fr" : "en"), [locale, setLocale]);
  const t = useCallback(
    (key: Key | string) => DICT[locale][key as Key] ?? EN[key as Key] ?? key,
    [locale],
  );

  return (
    <I18nContext.Provider value={{ locale, setLocale, toggle, t }}>{children}</I18nContext.Provider>
  );
}

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    // Fallback when used outside the provider (e.g. isolated tests): English, no persistence.
    return { locale: "en", setLocale: () => {}, toggle: () => {}, t: (k) => EN[k as Key] ?? k };
  }
  return ctx;
}

export function useT(): (key: Key | string) => string {
  return useI18n().t;
}
