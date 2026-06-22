"use client";

import { useEffect, useState } from "react";
import { getRoles, initAuth, isGuided } from "@/lib/auth";

function Forbidden() {
  return (
    <div
      data-testid="auth-forbidden"
      className="flex min-h-[40vh] items-center justify-center bg-white text-xs text-ink-secondary"
    >
      403 — insufficient role for this view
    </div>
  );
}

function KeycloakAuthGuard({
  children,
  roles,
  simulateRole,
}: {
  children: React.ReactNode;
  roles: string[];
  simulateRole?: string;
}) {
  const [ready, setReady] = useState(false);
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    initAuth().then((ok) => {
      setReady(true);
      setAllowed(ok && roleAllowed(roles, simulateRole));
    });
  }, [roles, simulateRole]);

  if (!ready) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center bg-white text-xs text-ink-secondary">
        Authenticating…
      </div>
    );
  }

  if (!allowed) return <Forbidden />;
  return <>{children}</>;
}

function activeRoles(simulateRole?: string): string[] {
  if (simulateRole) return [simulateRole];
  return [...getRoles()];
}

function roleAllowed(required: string[], simulateRole?: string): boolean {
  const mine = new Set(activeRoles(simulateRole));
  return required.some((r) => mine.has(r));
}

export function AuthGuard({
  children,
  roles,
  simulateRole,
}: {
  children: React.ReactNode;
  roles: string[];
  simulateRole?: string;
}) {
  if (isGuided()) {
    if (!roleAllowed(roles, simulateRole)) return <Forbidden />;
    return <>{children}</>;
  }
  return (
    <KeycloakAuthGuard roles={roles} simulateRole={simulateRole}>
      {children}
    </KeycloakAuthGuard>
  );
}
