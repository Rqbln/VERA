import { DashboardShell } from "@/components/DashboardShell";

export default function DashboardsLayout({ children }: { children: React.ReactNode }) {
  return <DashboardShell>{children}</DashboardShell>;
}
