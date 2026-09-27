import { useState } from "react";

export interface Bar {
  key: string;
  label: string;
  sublabel?: string;
  value: number; // 0..1
  detail: string; // shown on hover/focus and in the table view
}

/**
 * Sorted horizontal bars for one measure (dataviz: magnitude -> bar, one hue).
 * Each bar is direct-labeled; hover or focus shows the detail; a table view is one click away.
 */
export function BarList({ bars, valueLabel, caption }: { bars: Bar[]; valueLabel: string; caption: string }) {
  const [active, setActive] = useState<string | null>(null);
  const [asTable, setAsTable] = useState(false);

  return (
    <figure className="barlist">
      <div className="card-header">
        <figcaption className="small">{caption}</figcaption>
        <button type="button" className="btn btn-secondary btn-small" onClick={() => setAsTable((t) => !t)} aria-pressed={asTable}>
          {asTable ? "Show chart" : "Show table"}
        </button>
      </div>

      {asTable ? (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th scope="col">Section</th>
                <th scope="col">{valueLabel}</th>
                <th scope="col">Detail</th>
              </tr>
            </thead>
            <tbody>
              {bars.map((b) => (
                <tr key={b.key}>
                  <td>
                    {b.label}
                    {b.sublabel && <div className="small">{b.sublabel}</div>}
                  </td>
                  <td className="num">{Math.round(b.value * 100)}%</td>
                  <td className="small">{b.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <ul className="bars" role="list">
          {bars.map((b) => {
            const pct = Math.round(b.value * 100);
            return (
              <li
                key={b.key}
                className={`bar-row${active === b.key ? " is-active" : ""}`}
                tabIndex={0}
                onPointerEnter={() => setActive(b.key)}
                onPointerLeave={() => setActive(null)}
                onFocus={() => setActive(b.key)}
                onBlur={() => setActive(null)}
                aria-label={`${b.label}${b.sublabel ? `, ${b.sublabel}` : ""}: ${pct}% ${valueLabel.toLowerCase()}. ${b.detail}`}
              >
                <div className="bar-text">
                  <span className="bar-label">{b.label}</span>
                  {b.sublabel && <span className="small">{b.sublabel}</span>}
                </div>
                <div className="bar-plot">
                  <div className="bar-track">
                    {pct > 0 && <div className="bar-fill" style={{ width: `${pct}%` }} />}
                  </div>
                  <span className="bar-value">{pct}%</span>
                </div>
                {active === b.key && (
                  <div className="bar-tip" role="tooltip">
                    <strong>{pct}%</strong> {valueLabel.toLowerCase()} · {b.detail}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </figure>
  );
}
