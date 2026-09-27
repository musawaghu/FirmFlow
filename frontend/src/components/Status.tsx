import { PRIORITY_LABEL, PROGRESS_LABEL } from "../lib/format";
import type { Layer, Priority, ProgressStatus } from "../lib/types";
import { Icon } from "./Icon";

export function ProgressBadge({ status }: { status: ProgressStatus }) {
  const cls = status === "completed" ? "badge-active" : status === "in_progress" ? "badge-pending" : "badge-neutral";
  return (
    <span className={`badge ${cls}`}>
      {status === "completed" && <Icon name="check" size={12} />}
      {PROGRESS_LABEL[status]}
    </span>
  );
}

export function PriorityBadge({ priority }: { priority: Priority }) {
  return <span className="badge badge-inverse">{PRIORITY_LABEL[priority]}</span>;
}

export function LayerBadge({ layer, firmName }: { layer: Layer; firmName?: string | null }) {
  return <span className="badge badge-neutral">{layer === "baseline" ? "AEC baseline" : firmName || "Your firm"}</span>;
}

export function ErrorPanel({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="empty card">
      <Icon name="alert" size={28} />
      <p>{message}</p>
      {onRetry && (
        <button type="button" className="btn btn-secondary" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}
