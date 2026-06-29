"use client";

import Keycloak from "keycloak-js";

const keycloakConfig = {
  url: process.env.NEXT_PUBLIC_KEYCLOAK_URL || "http://localhost:8080",
  realm: process.env.NEXT_PUBLIC_KEYCLOAK_REALM || "vera",
  clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID || "vera-dashboard",
};

let keycloak: Keycloak | null = null;

// The single friendly persona used in guided (no-login) mode: holds every role so all lenses
// render for a non-technical user. Mirrors ALL_ROLES in the backend auth module.
export const GUIDED_ROLES = [
  "ml_researcher",
  "data_scientist",
  "secops",
  "domain_expert",
  "external_auditor",
  "legal_compliance",
  "risk_manager",
  "executive",
];

export function authMode(): string {
  return (process.env.NEXT_PUBLIC_AUTH_MODE || "guided").toLowerCase();
}

/** Guided no-login mode is the shipped default; enterprise mode enforces Keycloak. */
export function isGuided(): boolean {
  if (authMode() === "guided") return true;
  return process.env.NEXT_PUBLIC_AUTH_DISABLED === "1";
}

export function getKeycloak(): Keycloak {
  if (!keycloak) {
    keycloak = new Keycloak(keycloakConfig);
  }
  return keycloak;
}

export async function initAuth(): Promise<boolean> {
  if (isGuided()) return true;
  const kc = getKeycloak();
  try {
    const ok = await kc.init({
      onLoad: "login-required",
      pkceMethod: "S256",
      checkLoginIframe: false,
    });
    return !!ok;
  } catch {
    return false;
  }
}

export function getToken(): string | undefined {
  if (isGuided()) return undefined;
  return getKeycloak().token;
}

let roleOverride: string[] | null = null;

export function setRoleOverride(roles: string[] | null): void {
  roleOverride = roles;
}

export function getRoles(): string[] {
  if (roleOverride?.length) return roleOverride;
  if (isGuided()) {
    if (process.env.NEXT_PUBLIC_DEV_ROLES) {
      return process.env.NEXT_PUBLIC_DEV_ROLES.split(",").map((r) => r.trim());
    }
    return GUIDED_ROLES;
  }
  const kc = getKeycloak();
  return (kc.tokenParsed?.realm_access?.roles as string[]) || [];
}

export function hasAnyRole(roles: string[]): boolean {
  const mine = new Set(getRoles());
  return roles.some((r) => mine.has(r));
}

export const ROUTE_ROLES: Record<string, string[]> = {
  "/dashboards/compliance": [
    "legal_compliance",
    "risk_manager",
    "domain_expert",
    "external_auditor",
    "executive",
    "secops",
  ],
  "/dashboards/cyber": ["secops", "legal_compliance", "risk_manager", "external_auditor"],
  "/dashboards/ds": ["data_scientist", "ml_researcher"],
  "/inspector": [
    "secops",
    "legal_compliance",
    "external_auditor",
    "ml_researcher",
    "risk_manager",
  ],
};

export function logout(): void {
  getKeycloak().logout({ redirectUri: window.location.origin });
}
