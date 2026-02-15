import { FormEvent, useEffect, useMemo, useState } from "react";
import DOMPurify from "dompurify";
import { marked } from "marked";

import {
  createContent,
  deleteContent,
  getContent,
  gitStatus,
  listContent,
  login,
  logout,
  me,
  publish,
  updateContent
} from "./api";
import type { ContentSummary, EditorFormState, GitStatusItem, PublishResponse } from "./types";

type View = "dashboard" | "editor" | "publish";

const today = new Date().toISOString().slice(0, 10);

const emptyForm: EditorFormState = {
  type: "note",
  title: "",
  date: today,
  categories: "",
  draft: true,
  link: "",
  comment: "",
  body: ""
};

function App() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [view, setView] = useState<View>("dashboard");
  const [activeType, setActiveType] = useState<"note" | "post">("note");
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<ContentSummary[]>([]);
  const [form, setForm] = useState<EditorFormState>(emptyForm);
  const [statusMessage, setStatusMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [publishMessage, setPublishMessage] = useState("");
  const [gitFiles, setGitFiles] = useState<GitStatusItem[]>([]);
  const [publishResult, setPublishResult] = useState<PublishResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const previewHtml = useMemo(() => {
    return DOMPurify.sanitize(marked.parse(form.body || "") as string);
  }, [form.body]);

  async function bootstrap(): Promise<void> {
    try {
      await me();
      setLoggedIn(true);
      await refreshList(activeType, query);
      await refreshGitStatus();
    } catch {
      setLoggedIn(false);
    }
  }

  useEffect(() => {
    void bootstrap();
  }, []);

  async function refreshList(type = activeType, currentQuery = query): Promise<void> {
    const response = await listContent(type, currentQuery);
    setItems(response.items);
  }

  async function refreshGitStatus(): Promise<void> {
    const response = await gitStatus();
    setGitFiles(response.files);
  }

  function setField<K extends keyof EditorFormState>(key: K, value: EditorFormState[K]) {
    setForm((previous) => ({ ...previous, [key]: value }));
  }

  async function handleLogin(event: FormEvent): Promise<void> {
    event.preventDefault();
    setAuthError("");

    try {
      await login(password);
      setLoggedIn(true);
      setPassword("");
      await refreshList();
      await refreshGitStatus();
    } catch (error) {
      setAuthError((error as Error).message);
    }
  }

  async function handleLogout(): Promise<void> {
    try {
      await logout();
    } finally {
      setLoggedIn(false);
    }
  }

  async function handleSearch(): Promise<void> {
    setErrorMessage("");
    try {
      await refreshList();
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleOpen(item: ContentSummary): Promise<void> {
    setErrorMessage("");
    setStatusMessage("");
    try {
      const document = await getContent(item.id);
      const categories = (document.frontmatter.categories as string[] | undefined) ?? [];
      setForm({
        id: document.id,
        type: document.type,
        title: (document.frontmatter.title as string | undefined) ?? "",
        date: (document.frontmatter.date as string | undefined) ?? today,
        categories: categories.join(", "),
        draft: Boolean(document.frontmatter.draft ?? true),
        link: "",
        comment: "",
        body: document.body
      });
      setView("editor");
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  function validateForm(): string | null {
    if (!form.title.trim()) {
      return "Title is required";
    }
    if (form.link.trim()) {
      try {
        new URL(form.link.trim());
      } catch {
        return "Link must be a valid URL";
      }
    }
    return null;
  }

  async function handleSave(): Promise<void> {
    setLoading(true);
    setErrorMessage("");
    setStatusMessage("");

    const validationError = validateForm();
    if (validationError) {
      setErrorMessage(validationError);
      setLoading(false);
      return;
    }

    try {
      const saved = form.id ? await updateContent(form) : await createContent(form);
      setForm((previous) => ({ ...previous, id: saved.id, type: saved.type }));
      await refreshList(form.type, query);
      await refreshGitStatus();
      setStatusMessage("Content saved successfully.");
    } catch (error) {
      setErrorMessage((error as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(): Promise<void> {
    if (!form.id) {
      return;
    }

    const confirmFirst = window.confirm("Delete this file?");
    if (!confirmFirst) {
      return;
    }
    const confirmSecond = window.confirm("Confirm permanent deletion?");
    if (!confirmSecond) {
      return;
    }

    setLoading(true);
    setErrorMessage("");
    setStatusMessage("");

    try {
      await deleteContent(form.id);
      setForm({ ...emptyForm, type: activeType });
      setView("dashboard");
      await refreshList(activeType, query);
      await refreshGitStatus();
      setStatusMessage("Content deleted.");
    } catch (error) {
      setErrorMessage((error as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function handlePublish(): Promise<void> {
    setLoading(true);
    setErrorMessage("");
    setStatusMessage("");

    try {
      const result = await publish(publishMessage.trim() || undefined);
      setPublishResult(result);
      setPublishMessage("");
      await refreshGitStatus();
      await refreshList(activeType, query);
      setStatusMessage("Publish completed.");
    } catch (error) {
      setErrorMessage((error as Error).message);
    } finally {
      setLoading(false);
    }
  }

  function newDocument(type: "note" | "post"): void {
    setForm({ ...emptyForm, type });
    setView("editor");
    setErrorMessage("");
    setStatusMessage("");
  }

  if (!loggedIn) {
    return (
      <main className="page page-center">
        <section className="card auth-card">
          <h1>LLMDev CMS</h1>
          <p>Login required to manage posts and notes.</p>
          <form onSubmit={(event) => void handleLogin(event)}>
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
            {authError && <p className="error">{authError}</p>}
            <button type="submit">Login</button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="topbar">
        <h1>LLMDev CMS</h1>
        <nav>
          <button className={view === "dashboard" ? "active" : ""} onClick={() => setView("dashboard")}>
            Dashboard
          </button>
          <button className={view === "editor" ? "active" : ""} onClick={() => setView("editor")}>
            Editor
          </button>
          <button className={view === "publish" ? "active" : ""} onClick={() => setView("publish")}>
            Publish
          </button>
          <button onClick={() => void handleLogout()}>Logout</button>
        </nav>
      </header>

      {statusMessage && <p className="status">{statusMessage}</p>}
      {errorMessage && <p className="error">{errorMessage}</p>}

      {view === "dashboard" && (
        <section className="card">
          <div className="dashboard-actions">
            <div>
              <button className={activeType === "note" ? "active" : ""} onClick={() => setActiveType("note")}>
                Notes
              </button>
              <button className={activeType === "post" ? "active" : ""} onClick={() => setActiveType("post")}>
                Posts
              </button>
            </div>
            <div>
              <button onClick={() => newDocument(activeType)}>New {activeType}</button>
            </div>
          </div>

          <div className="search-row">
            <input
              placeholder="Search by title"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <button onClick={() => void handleSearch()}>Search</button>
          </div>

          <ul className="content-list">
            {items.map((item) => (
              <li key={item.id}>
                <div>
                  <strong>{item.title}</strong>
                  <span>{item.slug}.md</span>
                </div>
                <div className="list-meta">
                  <span>{item.date ?? "no-date"}</span>
                  <span>{item.draft ? "draft" : "published"}</span>
                  <button onClick={() => void handleOpen(item)}>Open</button>
                </div>
              </li>
            ))}
            {items.length === 0 && <li>No content found.</li>}
          </ul>
        </section>
      )}

      {view === "editor" && (
        <section className="editor-layout">
          <article className="card">
            <h2>{form.id ? "Edit content" : "New content"}</h2>
            <div className="form-grid">
              <label>
                Type
                <select value={form.type} onChange={(event) => setField("type", event.target.value as "note" | "post")}> 
                  <option value="note">Note</option>
                  <option value="post">Post</option>
                </select>
              </label>

              <label>
                Title
                <input value={form.title} onChange={(event) => setField("title", event.target.value)} required />
              </label>

              <label>
                Date
                <input type="date" value={form.date} onChange={(event) => setField("date", event.target.value)} />
              </label>

              <label>
                Categories (comma separated)
                <input value={form.categories} onChange={(event) => setField("categories", event.target.value)} />
              </label>

              <label>
                Link (optional)
                <input value={form.link} onChange={(event) => setField("link", event.target.value)} />
              </label>

              <label>
                Comment (optional)
                <textarea value={form.comment} onChange={(event) => setField("comment", event.target.value)} rows={3} />
              </label>

              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={form.draft}
                  onChange={(event) => setField("draft", event.target.checked)}
                />
                Draft
              </label>
            </div>

            <label>
              Markdown body
              <textarea
                className="editor-textarea"
                value={form.body}
                onChange={(event) => setField("body", event.target.value)}
                rows={20}
              />
            </label>

            <div className="button-row">
              <button onClick={() => void handleSave()} disabled={loading}>
                Save
              </button>
              <button onClick={() => setView("dashboard")} disabled={loading}>
                Back
              </button>
              <button onClick={() => void handleDelete()} disabled={!form.id || loading} className="danger">
                Delete
              </button>
            </div>
          </article>

          <article className="card preview-card">
            <h2>Preview</h2>
            <div className="preview" dangerouslySetInnerHTML={{ __html: previewHtml }} />
          </article>
        </section>
      )}

      {view === "publish" && (
        <section className="card">
          <h2>Publish</h2>
          <p>{gitFiles.length > 0 ? `${gitFiles.length} pending file(s)` : "No pending changes in content/"}</p>

          <ul className="content-list">
            {gitFiles.map((item) => (
              <li key={`${item.status}-${item.path}`}>
                <span>{item.status}</span>
                <span>{item.path}</span>
              </li>
            ))}
            {gitFiles.length === 0 && <li>Working tree clean for content/.</li>}
          </ul>

          <label>
            Commit message (optional)
            <input value={publishMessage} onChange={(event) => setPublishMessage(event.target.value)} />
          </label>

          <div className="button-row">
            <button onClick={() => void refreshGitStatus()}>Refresh status</button>
            <button onClick={() => void handlePublish()} disabled={gitFiles.length === 0 || loading}>
              Publish (commit + push)
            </button>
          </div>

          {publishResult && (
            <div className="publish-result">
              <p>
                <strong>Commit:</strong> {publishResult.commit_hash}
              </p>
              <p>
                <strong>Message:</strong> {publishResult.message}
              </p>
              <pre>{publishResult.output || "No git output."}</pre>
            </div>
          )}
        </section>
      )}
    </main>
  );
}

export default App;
