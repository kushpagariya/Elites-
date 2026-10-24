import type { ReactNode } from "react";
import { WorkspaceProvider } from "@/lib/workspace";
import WorkspaceShell from "@/components/WorkspaceShell";
import "maplibre-gl/dist/maplibre-gl.css";
import "./workspace.css";
export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="workspace">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <WorkspaceProvider>
        <WorkspaceShell>{children}</WorkspaceShell>
      </WorkspaceProvider>
    </div>
  );
}
