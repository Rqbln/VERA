"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

// Lightweight bilingual layer (FR/EN). Technical acronyms (EU AI Act, COMPL-AI, LLM, RBAC, HITL,
// CI, Trust Factor, GaaS) are intentionally kept identical in both locales. Components opt in via
// useT(); any component that does not is simply rendered in its source language.

export type Locale = "en" | "fr";

const EN = {
  "app.title": "VERA Control Room",
  "nav.home": "Home",
  "nav.launch": "Launch evaluation",
  "nav.runs": "Runs",
  "nav.governance": "Governance",
  "nav.compliance": "Compliance",
  "nav.cyber": "Cyber",
  "nav.ds": "Data Science",
  "nav.guided": "Guided mode · no login",
  "nav.signout": "Sign out",

  "home.welcome": "Welcome to VERA",
  "home.intro":
    "VERA checks whether an AI model meets the EU AI Act requirements. Launch an evaluation on a connected model and read a clear summary — no code, no login.",
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
    "Continuous, auditable oversight of governed inference. Modes: shadow observes, advisory alerts, enforcement blocks.",
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

  "summary.gov_trends": "Governance & trends",
  "summary.header": "Run summary",
  "summary.inspector": "Inspector →",
  "summary.trust_factor": "Trust Factor",
  "summary.weakest": "Weakest requirements",
  "summary.count.failed": "Failed",
  "summary.count.fallback": "Fallback",
  "summary.count.ok": "OK",
  "summary.count.uncovered": "Uncovered",
  "summary.band.green": "Compliant",
  "summary.band.orange": "Watch",
  "summary.band.red": "Action needed",
  "summary.band.unknown": "Not available",
  "summary.run_details": "Run details",
  "summary.lifecycle": "Lifecycle",
  "summary.catalog": "Catalog",
  "summary.coverage": "COMPL-AI coverage",
  "summary.provenance": "Harness provenance",
  "summary.select_run": "Select a run to view COMPL-AI triage.",

  "hitl.title": "Human review (N01 / N02)",
  "hitl.add_n01": "+ N01 explainability",
  "hitl.add_n02": "+ N02 corrigibility",
  "hitl.empty": "No review tasks yet. N01/N02 require a human panel; queue one above.",
  "hitl.submit": "Submit",
  "hitl.comment_placeholder": "Comment (optional)",
  "hitl.avg_preview": "avg",
  "hitl.likert": "Likert",

  "nm.title": "Non-measurable (N01–N06)",
  "nm.reviewed": "reviewed",
  "nm.caption":
    "N01/N02 from the HITL review queue · N03 measured (CodeCarbon) · N04–N06 from the declarative forms",
  "nm.n01": "Explainability",
  "nm.n02": "Corrigibility",
  "nm.n03": "Environmental impact",
  "nm.n04": "Datasheet / model card",
  "nm.n05": "Evaluation summary",
  "nm.n06": "Risk summary",

  "forms.title": "Declarative forms (N03–N06)",
  "forms.mark_completed": "Mark as completed",
  "forms.save": "Save form",
  "forms.saving": "Saving…",
  "forms.save_failed": "Save failed (compliance role required in enterprise mode).",

  "study.title": "VERA user study",
  "study.intro.heading": "Reading an evaluation run",
  "study.intro.consent":
    "You will answer eight questions using the VERA dashboard, then a short questionnaire about the tool. The time you spend on each task is recorded by the application. No name or personal data is collected: only a participant code, your role, and three background questions. Results are reported in aggregate in a research paper.",
  "study.intro.consent_check": "I agree to participate",
  "study.intro.role": "Your role",
  "study.intro.ai_experience": "Your experience with AI/ML models",
  "study.ai_exp.none": "I have never worked with AI/ML models",
  "study.ai_exp.user": "I use AI tools but do not build or evaluate models",
  "study.ai_exp.reviewer": "I review or assess AI/ML models as part of my job",
  "study.ai_exp.builder": "I build, train or evaluate AI/ML models myself",
  "study.intro.aiact": "Your familiarity with the EU AI Act",
  "study.aiact.none": "Not familiar with it",
  "study.aiact.heard": "I have heard of it but never worked with it",
  "study.aiact.working": "Working knowledge (read parts, applied it occasionally)",
  "study.aiact.expert": "I work with it regularly (compliance or legal responsibility)",
  "study.intro.seniority": "Years of professional experience",
  "study.seniority.lt2": "Less than 2 years",
  "study.seniority.2to5": "2 to 5 years",
  "study.seniority.6to10": "6 to 10 years",
  "study.seniority.gt10": "More than 10 years",
  "study.intro.begin": "Begin the study",
  "study.role.compliance_officer": "Compliance officer",
  "study.role.risk_manager": "Risk manager",
  "study.role.legal": "Legal",
  "study.role.audit": "Audit",
  "study.role.ai_researcher": "AI researcher",
  "study.role.other_non_ml": "Other (non-ML)",
  "study.progress": "Task",
  "study.of": "of",
  "study.start": "Start this task",
  "study.submit": "Submit answer",
  "study.giveup": "Give up",
  "study.giveup_confirm": "Confirm give up",
  "study.open_dashboard": "Open the dashboard",
  "study.recording": "recording",
  "study.timeout_note": "Time limit reached for this task; moving on.",
  "study.t1.instruction": "Which requirement is the model weakest on?",
  "study.t1.label": "Requirement",
  "study.t2.instruction": "For that requirement, what is its score and its confidence interval?",
  "study.t2.score": "Score",
  "study.t2.ci_lower": "CI lower bound",
  "study.t2.ci_upper": "CI upper bound",
  "study.t3.instruction": "Which checks ran in a degraded (fallback) mode?",
  "study.t4.instruction": "How many of the twelve requirements were evaluated in this run?",
  "study.t4.label": "Count",
  "study.t5.instruction": "Find one actual model answer that contributed to a score, and paste a fragment of it below.",
  "study.t5.placeholder": "Paste a fragment of the model output here…",
  "study.t5.confirm": "I found this in the dashboard",
  "study.t6.instruction": "How many requirements failed, how many are in fallback, how many are OK?",
  "study.t6.failed": "Failed",
  "study.t6.fallback": "Fallback",
  "study.t6.ok": "OK",
  "study.t7.instruction": "What is the overall Trust Factor, and is it compliant, watch, or action needed?",
  "study.t7.score": "Trust Factor (0-100)",
  "study.t7.band": "Verdict",
  "study.t8.instruction": "Launch a new evaluation on the recommended model with the recommended settings, then paste the address of the page you land on.",
  "study.t8.label": "Run page address (URL)",
  "study.survey.heading": "One last step: your view of the tool",
  "study.survey.intro":
    "Eight statements about VERA. There is no right answer; we are measuring your impression after using it.",
  "study.survey.scale_hint": "1 = strongly disagree, 5 = strongly agree",
  "study.survey.pu_heading": "Usefulness",
  "study.survey.peou_heading": "Ease of use",
  "study.survey.likert.1": "Strongly disagree",
  "study.survey.likert.2": "Disagree",
  "study.survey.likert.3": "Neutral",
  "study.survey.likert.4": "Agree",
  "study.survey.likert.5": "Strongly agree",
  "study.survey.pu1":
    "Using VERA would help me evaluate an AI model faster than my current way of working.",
  "study.survey.pu2": "VERA helps me understand why a model fails a requirement.",
  "study.survey.pu3":
    "VERA would help me justify a deployment decision to a third party (management, audit, regulator).",
  "study.survey.pu4": "Using VERA would improve the quality of an AI model evaluation.",
  "study.survey.peou1": "The VERA interface is clear and easy to read.",
  "study.survey.peou2": "I knew where to find the information I needed.",
  "study.survey.peou3": "I could launch an evaluation on my own, without help.",
  "study.survey.peou4": "Learning to use VERA would require little effort from me.",
  "study.survey.comment": "Anything else you would like to tell us? (optional)",
  "study.survey.comment_placeholder": "What worked, what did not…",
  "study.survey.comment_privacy":
    "Please do not include names, your employer, or any personal data.",
  "study.survey.submit": "Finish",
  "study.survey.remaining": "statement(s) left",
  "study.done.title": "Thank you!",
  "study.done.body": "Your answers are recorded. You can close this tab.",
  "study.error": "Something went wrong; please tell the study organiser.",

  "common.status": "Status",
  "common.model": "Model",
  "common.loading": "Loading…",
  "lang.toggle": "FR",
} as const;

type Key = keyof typeof EN;

const FR: Record<Key, string> = {
  "app.title": "VERA — Salle de pilotage",
  "nav.home": "Accueil",
  "nav.launch": "Lancer une évaluation",
  "nav.runs": "Évaluations",
  "nav.governance": "Gouvernance",
  "nav.compliance": "Conformité",
  "nav.cyber": "Cyber",
  "nav.ds": "Data Science",
  "nav.guided": "Mode guidé · sans connexion",
  "nav.signout": "Se déconnecter",

  "home.welcome": "Bienvenue dans VERA",
  "home.intro":
    "VERA vérifie si un modèle d’IA respecte les exigences de l’EU AI Act. Lancez une évaluation sur un modèle connecté et lisez un résumé clair — sans code, sans connexion.",
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
    "Supervision continue et auditable de l’inférence gouvernée. Modes : shadow observe, advisory alerte, enforcement bloque.",
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

  "summary.gov_trends": "Gouvernance & tendances",
  "summary.header": "Synthèse d'évaluation",
  "summary.inspector": "Inspecteur →",
  "summary.trust_factor": "Trust Factor",
  "summary.weakest": "Exigences les plus faibles",
  "summary.count.failed": "Échec",
  "summary.count.fallback": "Repli",
  "summary.count.ok": "OK",
  "summary.count.uncovered": "Non couvertes",
  "summary.band.green": "Conforme",
  "summary.band.orange": "À surveiller",
  "summary.band.red": "Action requise",
  "summary.band.unknown": "Indisponible",
  "summary.run_details": "Détails de l'évaluation",
  "summary.lifecycle": "Cycle de vie",
  "summary.catalog": "Catalogue",
  "summary.coverage": "Couverture COMPL-AI",
  "summary.provenance": "Provenance des harnais",
  "summary.select_run": "Sélectionnez une évaluation pour voir le triage COMPL-AI.",

  "hitl.title": "Revue humaine (N01 / N02)",
  "hitl.add_n01": "+ N01 explicabilité",
  "hitl.add_n02": "+ N02 corrigibilité",
  "hitl.empty": "Aucune tâche de revue. N01/N02 requièrent un panel humain ; ajoutez-en une ci-dessus.",
  "hitl.submit": "Soumettre",
  "hitl.comment_placeholder": "Commentaire (optionnel)",
  "hitl.avg_preview": "moy.",
  "hitl.likert": "Likert",

  "nm.title": "Non mesurables (N01–N06)",
  "nm.reviewed": "revues",
  "nm.caption":
    "N01/N02 depuis la file de revue HITL · N03 mesuré (CodeCarbon) · N04–N06 depuis les formulaires déclaratifs",
  "nm.n01": "Explicabilité",
  "nm.n02": "Corrigibilité",
  "nm.n03": "Impact environnemental",
  "nm.n04": "Datasheet / model card",
  "nm.n05": "Résumé des évaluations",
  "nm.n06": "Résumé des risques",

  "forms.title": "Formulaires déclaratifs (N03–N06)",
  "forms.mark_completed": "Marquer comme complété",
  "forms.save": "Enregistrer",
  "forms.saving": "Enregistrement…",
  "forms.save_failed": "Échec (rôle conformité requis en mode entreprise).",

  "study.title": "Étude utilisateur VERA",
  "study.intro.heading": "Lire une évaluation",
  "study.intro.consent":
    "Vous répondrez à huit questions à l'aide du tableau de bord VERA, puis à un court questionnaire sur l'outil. Le temps passé sur chaque tâche est mesuré par l'application. Aucun nom ni donnée personnelle n'est collecté : seulement un code participant, votre rôle et trois questions de contexte. Les résultats sont rapportés de façon agrégée dans un article de recherche.",
  "study.intro.consent_check": "J'accepte de participer",
  "study.intro.role": "Votre rôle",
  "study.intro.ai_experience": "Votre expérience des modèles d'IA/ML",
  "study.ai_exp.none": "Je n'ai jamais travaillé sur des modèles d'IA/ML",
  "study.ai_exp.user": "J'utilise des outils d'IA mais je ne construis ni n'évalue de modèles",
  "study.ai_exp.reviewer": "J'examine ou j'évalue des modèles d'IA/ML dans mon travail",
  "study.ai_exp.builder": "Je construis, entraîne ou évalue moi-même des modèles d'IA/ML",
  "study.intro.aiact": "Votre connaissance de l'AI Act européen",
  "study.aiact.none": "Je ne le connais pas",
  "study.aiact.heard": "J'en ai entendu parler mais je n'ai jamais travaillé avec",
  "study.aiact.working": "Connaissance pratique (j'en ai lu des parties, appliqué à l'occasion)",
  "study.aiact.expert": "Je travaille avec régulièrement (responsabilité conformité ou juridique)",
  "study.intro.seniority": "Années d'expérience professionnelle",
  "study.seniority.lt2": "Moins de 2 ans",
  "study.seniority.2to5": "2 à 5 ans",
  "study.seniority.6to10": "6 à 10 ans",
  "study.seniority.gt10": "Plus de 10 ans",
  "study.intro.begin": "Commencer l'étude",
  "study.role.compliance_officer": "Responsable conformité",
  "study.role.risk_manager": "Risk manager",
  "study.role.legal": "Juridique",
  "study.role.audit": "Audit",
  "study.role.ai_researcher": "Chercheur en IA",
  "study.role.other_non_ml": "Autre (non-ML)",
  "study.progress": "Tâche",
  "study.of": "sur",
  "study.start": "Démarrer cette tâche",
  "study.submit": "Envoyer la réponse",
  "study.giveup": "Abandonner",
  "study.giveup_confirm": "Confirmer l'abandon",
  "study.open_dashboard": "Ouvrir le tableau de bord",
  "study.recording": "enregistrement",
  "study.timeout_note": "Temps limite atteint pour cette tâche ; on passe à la suivante.",
  "study.t1.instruction": "Sur quelle exigence le modèle est-il le plus faible ?",
  "study.t1.label": "Exigence",
  "study.t2.instruction": "Pour cette exigence, quel est son score et son intervalle de confiance ?",
  "study.t2.score": "Score",
  "study.t2.ci_lower": "Borne basse de l'IC",
  "study.t2.ci_upper": "Borne haute de l'IC",
  "study.t3.instruction": "Quels contrôles ont tourné en mode dégradé (fallback) ?",
  "study.t4.instruction": "Combien des douze exigences ont été évaluées dans ce run ?",
  "study.t4.label": "Nombre",
  "study.t5.instruction": "Trouvez une vraie réponse du modèle ayant contribué à un score, et collez-en un fragment ci-dessous.",
  "study.t5.placeholder": "Collez ici un fragment de la sortie du modèle…",
  "study.t5.confirm": "Je l'ai trouvée dans le tableau de bord",
  "study.t6.instruction": "Combien d'exigences en échec, combien en fallback, combien OK ?",
  "study.t6.failed": "Échec",
  "study.t6.fallback": "Fallback",
  "study.t6.ok": "OK",
  "study.t7.instruction": "Quel est le Trust Factor global, et est-il conforme, à surveiller, ou action requise ?",
  "study.t7.score": "Trust Factor (0-100)",
  "study.t7.band": "Verdict",
  "study.t8.instruction": "Lancez une nouvelle évaluation sur le modèle recommandé avec les réglages recommandés, puis collez l'adresse de la page d'arrivée.",
  "study.t8.label": "Adresse de la page du run (URL)",
  "study.survey.heading": "Dernière étape : votre avis sur l'outil",
  "study.survey.intro":
    "Huit affirmations sur VERA. Il n'y a pas de bonne réponse : nous mesurons votre impression après usage.",
  "study.survey.scale_hint": "1 = pas du tout d'accord, 5 = tout à fait d'accord",
  "study.survey.pu_heading": "Utilité",
  "study.survey.peou_heading": "Facilité d'usage",
  "study.survey.likert.1": "Pas du tout d'accord",
  "study.survey.likert.2": "Plutôt pas d'accord",
  "study.survey.likert.3": "Neutre",
  "study.survey.likert.4": "Plutôt d'accord",
  "study.survey.likert.5": "Tout à fait d'accord",
  "study.survey.pu1":
    "Utiliser VERA me permettrait d'évaluer un modèle d'IA plus rapidement qu'avec ma façon de travailler actuelle.",
  "study.survey.pu2": "VERA m'aide à comprendre pourquoi un modèle échoue sur une exigence.",
  "study.survey.pu3":
    "VERA m'aiderait à justifier une décision de mise en production auprès d'un tiers (direction, audit, régulateur).",
  "study.survey.pu4": "Utiliser VERA améliorerait la qualité de l'évaluation d'un modèle d'IA.",
  "study.survey.peou1": "L'interface de VERA est claire et facile à lire.",
  "study.survey.peou2": "Je savais où trouver l'information dont j'avais besoin.",
  "study.survey.peou3": "Je pourrais lancer une évaluation seul(e), sans aide.",
  "study.survey.peou4": "Apprendre à utiliser VERA me demanderait peu d'efforts.",
  "study.survey.comment": "Autre chose à nous dire ? (facultatif)",
  "study.survey.comment_placeholder": "Ce qui a marché, ce qui n'a pas marché…",
  "study.survey.comment_privacy":
    "Merci de ne pas indiquer de noms, votre employeur, ni aucune donnée personnelle.",
  "study.survey.submit": "Terminer",
  "study.survey.remaining": "affirmation(s) restante(s)",
  "study.done.title": "Merci !",
  "study.done.body": "Vos réponses sont enregistrées. Vous pouvez fermer cet onglet.",
  "study.error": "Un problème est survenu ; signalez-le à l'organisateur de l'étude.",

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
    const saved = typeof window !== "undefined" ? (localStorage.getItem("vera-locale") as Locale | null) : null;
    if (saved === "fr" || saved === "en") setLocaleState(saved);
  }, []);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    if (typeof window !== "undefined") localStorage.setItem("vera-locale", l);
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
