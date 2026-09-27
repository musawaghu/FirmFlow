import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Icon } from "../../components/Icon";
import { ErrorPanel } from "../../components/Status";
import { api } from "../../lib/api";
import { shortDate } from "../../lib/format";
import type { Manual } from "../../lib/types";
import { useLoad } from "../../lib/useLoad";

const MAX_BYTES = 25 * 1024 * 1024; // backend: 25 MB

export const MANUAL_STATUS: Record<Manual["status"], { label: string; cls: string }> = {
  uploaded: { label: "Ready to process", cls: "badge-neutral" },
  processing: { label: "Processing", cls: "badge-pending" },
  processed: { label: "Ready to review", cls: "badge-active" },
  failed: { label: "Failed", cls: "badge-pending" },
};

export function Manuals() {
  const { data: manuals, error, reload } = useLoad(api.manuals);
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const pick = (f: File | null) => {
    setUploadError(null);
    if (f && !/\.(pdf|docx)$/i.test(f.name)) {
      setUploadError("Choose a PDF or Word (.docx) file.");
      f = null;
    } else if (f && f.size > MAX_BYTES) {
      setUploadError("The file is larger than 25 MB.");
      f = null;
    }
    setFile(f);
    if (f && !title) setTitle(f.name.replace(/\.(pdf|docx)$/i, ""));
  };

  const upload = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      const manual = await api.uploadManual(file, title);
      navigate(`/admin/manuals/${manual.id}`);
    } catch (err) {
      setUploadError((err as Error).message);
      setUploading(false);
    }
  };

  return (
    <>
      <div className="page-head">
        <h1>Manuals</h1>
        <p className="lede">
          Upload your firm&rsquo;s handbook. Claude turns it into draft modules and flags problems in it, and you review each module next to the original
          before new hires see it.
        </p>
      </div>

      <form className="card card-alt" onSubmit={upload} aria-labelledby="upload-title">
        <div className="card-header">
          <h2 id="upload-title">Upload a manual</h2>
          <Icon name="book" size={22} />
        </div>
        <div
          className={`dropzone${file ? " has-file" : ""}`}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            pick(e.dataTransfer.files[0] ?? null);
          }}
        >
          <input
            id="manual-file"
            type="file"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            className="sr-only"
            onChange={(e) => pick(e.target.files?.[0] ?? null)}
          />
          {file ? (
            <span className="status-row">
              <Icon name="check" />
              <strong>{file.name}</strong>
              <span className="small">({(file.size / 1024 / 1024).toFixed(1)} MB)</span>
            </span>
          ) : (
            <span>Drop a PDF or Word file here, or</span>
          )}
          <label htmlFor="manual-file" className="btn btn-secondary btn-small">
            {file ? "Choose a different file" : "Choose a file"}
          </label>
          <span className="small">PDF or DOCX, up to 25 MB and 200 pages.</span>
        </div>
        <div className="field">
          <label htmlFor="manual-title">Title</label>
          <input id="manual-title" className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Studio Handbook 2026" />
        </div>
        {uploadError && (
          <p className="form-error" role="alert">
            {uploadError}
          </p>
        )}
        <div>
          <button type="submit" className="btn btn-primary" disabled={!file || uploading}>
            {uploading ? "Uploading and reading the file…" : "Upload"}
          </button>
        </div>
      </form>

      <section className="stack" aria-labelledby="manuals-title">
        <h2 id="manuals-title">Your manuals</h2>
        {error ? (
          <ErrorPanel message={error} onRetry={reload} />
        ) : !manuals ? (
          <div className="empty">Loading…</div>
        ) : manuals.length === 0 ? (
          <div className="card empty">
            <p>No manuals yet. Upload one above.</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Title</th>
                  <th scope="col">File</th>
                  <th scope="col">Status</th>
                  <th scope="col">Uploaded</th>
                  <th scope="col">
                    <span className="sr-only">Open</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {manuals.map((m) => (
                  <tr key={m.id}>
                    <td>
                      <strong>{m.title}</strong>
                    </td>
                    <td>
                      {m.file_type.toUpperCase()}
                      {m.page_count ? `, ${m.page_count} pages` : ""}
                    </td>
                    <td>
                      <span className={`badge ${MANUAL_STATUS[m.status].cls}`}>{MANUAL_STATUS[m.status].label}</span>
                    </td>
                    <td>{shortDate(m.created_at)}</td>
                    <td>
                      <Link to={`/admin/manuals/${m.id}`}>{m.status === "processed" ? "Review" : "Open"}</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
