import type { ReactNode } from "react";
import { WorkspaceProvider } from "@/lib/workspace";
import WorkspaceShell from "@/components/WorkspaceShell";
import AuthGate from "@/components/AuthGate";
import "maplibre-gl/dist/maplibre-gl.css";
import "./workspace.css";
import "./workspace-refresh.css";
export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="workspace">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <AuthGate><WorkspaceProvider>
        <WorkspaceShell>{children}</WorkspaceShell>
      </WorkspaceProvider></AuthGate>
    </div>
  );
}
