import type { ReactNode } from "react";

// Renders the small Markdown subset the enhancer writes: paragraphs, "- " and "1. "
// lists, pipe tables, **bold**, and bare URLs. Builds React elements (never HTML
// strings), so passage text can't inject markup.

type Block =
  | { type: "p"; lines: string[] }
  | { type: "ul" | "ol"; items: string[] }
  | { type: "table"; head: string[]; rows: string[][] };

const BULLET = /^\s*[-*•]\s+/;
const NUMBERED = /^\s*\d+[.)]\s+/;
const TABLE_ROW = /^\s*\|.*\|\s*$/;
const TABLE_RULE = /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/;

function cells(row: string): string[] {
  return row.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());
}

function parse(text: string): Block[] {
  const blocks: Block[] = [];
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) {
      i++;
      continue;
    }
    if (TABLE_ROW.test(line) && i + 1 < lines.length && TABLE_RULE.test(lines[i + 1])) {
      const head = cells(line);
      const rows: string[][] = [];
      i += 2;
      while (i < lines.length && TABLE_ROW.test(lines[i])) rows.push(cells(lines[i++]));
      blocks.push({ type: "table", head, rows });
      continue;
    }
    const listType = BULLET.test(line) ? "ul" : NUMBERED.test(line) ? "ol" : null;
    if (listType) {
      const marker = listType === "ul" ? BULLET : NUMBERED;
      const items: string[] = [];
      while (i < lines.length && lines[i].trim()) {
        if (marker.test(lines[i])) items.push(lines[i].replace(marker, ""));
        else if (items.length) items[items.length - 1] += ` ${lines[i].trim()}`; // wrapped continuation
        else break;
        i++;
      }
      blocks.push({ type: listType, items });
      continue;
    }
    const para: string[] = [];
    while (i < lines.length && lines[i].trim() && !BULLET.test(lines[i]) && !NUMBERED.test(lines[i]) && !TABLE_ROW.test(lines[i])) {
      para.push(lines[i++]);
    }
    blocks.push({ type: "p", lines: para });
  }
  return blocks;
}

const INLINE = /(\*\*[^*]+\*\*|https?:\/\/[^\s)]+)/g;

function inline(text: string): ReactNode[] {
  return text.split(INLINE).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) return <strong key={i}>{part.slice(2, -2)}</strong>;
    if (/^https?:\/\//.test(part)) {
      const url = part.replace(/[.,;:]$/, "");
      return (
        <a key={i} href={url} target="_blank" rel="noreferrer noopener">
          {url}
        </a>
      );
    }
    return part;
  });
}

export function PassageText({ text }: { text: string }) {
  return (
    <div className="prose">
      {parse(text).map((b, i) => {
        if (b.type === "p") {
          return (
            <p key={i}>
              {b.lines.map((l, j) => (
                <span key={j}>
                  {j > 0 && <br />}
                  {inline(l)}
                </span>
              ))}
            </p>
          );
        }
        if (b.type === "table") {
          return (
            <div key={i} className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    {b.head.map((h, j) => (
                      <th key={j} scope="col">
                        {inline(h)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {b.rows.map((r, j) => (
                    <tr key={j}>
                      {r.map((c, k) => (
                        <td key={k}>{inline(c)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
        const List = b.type;
        return (
          <List key={i}>
            {b.items.map((it, j) => (
              <li key={j}>{inline(it)}</li>
            ))}
          </List>
        );
      })}
    </div>
  );
}
