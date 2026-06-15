"use client";

import Keycloak from "keycloak-js";

const keycloakConfig = {
  url: process.env.NEXT_PUBLIC_KEYCLOAK_URL || "http://localhost:8080",
  realm: process.env.NEXT_PUBLIC_KEYCLOAK_REALM || "raip",
  clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID || "raip-dashboard",
};

let keycloak: Keycloak | null = null;

export function getKeycloak(): Keycloak {
  if (!keycloak) {
    keycloak = new Keycloak(keycloakConfig);
  }
  return keycloak;
}

export async function initAuth(): Promise<boolean> {
  const kc = getKeycloak();
  const authDisabled = process.env.NEXT_PUBLIC_AUTH_DISABLED === "1";
  if (authDisabled) return true;
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
  if (process.env.NEXT_PUBLIC_AUTH_DISABLED === "1") return undefined;
  return getKeycloak().token;
}

let roleOverride: string[] | null = null;

export function setRoleOverride(roles: string[] | null): void {
  roleOverride = roles;
}

export function getRoles(): string[] {
  if (roleOverride?.length) return roleOverride;
  if (process.env.NEXT_PUBLIC_AUTH_DISABLED === "1") {
    return (process.env.NEXT_PUBLIC_DEV_ROLES || "legal_compliance").split(",");
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
