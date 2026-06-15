import { DashboardShell } from "@/components/DashboardShell";

export default function ConsoleLayout({ children }: { children: React.ReactNode }) {
  return <DashboardShell>{children}</DashboardShell>;
}
