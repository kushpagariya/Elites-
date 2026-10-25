import type { Diagnosis } from "@/lib/types";
import { statusLabel } from "@/lib/presentation";
export default function StatusBadge({ status }: { status?: Diagnosis }) {
  return (
    <span
      className={"diagnosis diagnosis-" + (status?.toLowerCase() ?? "unknown")}
    >
      {statusLabel(status)}
    </span>
  );
}
