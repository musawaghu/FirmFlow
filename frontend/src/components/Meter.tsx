import { percent } from "../lib/format";

/**
 * A ratio against a whole (dataviz: meter, not a pie). The fill is the accent,
 * the track is off-white, and the value is always printed, so nothing is color-only.
 */
export function Meter({ label, done, total, size = "md" }: { label: string; done: number; total: number; size?: "sm" | "md" }) {
  const pct = percent(done, total);
  return (
    <div className={`meter meter-${size}`}>
      <div className="meter-head">
        <span className="meter-label">{label}</span>
        <span className="meter-value">
          {done} of {total}
          <span className="sr-only"> ({pct}%)</span>
        </span>
      </div>
      <div className="meter-track" role="meter" aria-label={label} aria-valuemin={0} aria-valuemax={total} aria-valuenow={done} title={`${label}: ${done} of ${total} (${pct}%)`}>
        {pct > 0 && <div className="meter-fill" style={{ width: `${pct}%` }} />}
      </div>
    </div>
  );
}
