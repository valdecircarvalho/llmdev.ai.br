import type {
  AuthToken,
  ContentDocument,
  ContentListResponse,
  EditorFormState,
  GitStatusResponse,
  PublishResponse
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";
const TOKEN_KEY = "cms_token";

function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

function saveToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers ?? {});
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    credentials: "include"
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(payload.detail ?? `Request failed (${response.status})`);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export async function login(password: string): Promise<void> {
  const data = await request<AuthToken>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ password })
  });
  saveToken(data.access_token);
}

export async function logout(): Promise<void> {
  await request("/auth/logout", { method: "POST" });
  clearToken();
}

export async function me(): Promise<{ user: string }> {
  return request<{ user: string }>("/auth/me");
}

export async function listContent(type: "note" | "post", query: string): Promise<ContentListResponse> {
  const search = new URLSearchParams({ type, query, page: "1", page_size: "100" });
  return request<ContentListResponse>(`/content?${search.toString()}`);
}

export async function getContent(id: string): Promise<ContentDocument> {
  return request<ContentDocument>(`/content/${encodeURIComponent(id).replace(/%2F/g, "/")}`);
}

function toPayload(form: EditorFormState): Record<string, unknown> {
  const categories = form.categories
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  const payload: Record<string, unknown> = {
    title: form.title,
    date: form.date,
    categories,
    draft: form.draft,
    body: form.body,
    link: form.link || undefined,
    comment: form.comment || undefined
  };

  return payload;
}

export async function createContent(form: EditorFormState): Promise<ContentDocument> {
  const payload = {
    ...toPayload(form),
    type: form.type
  };

  return request<ContentDocument>("/content", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function updateContent(form: EditorFormState): Promise<ContentDocument> {
  if (!form.id) {
    throw new Error("ID is required to update content");
  }

  return request<ContentDocument>(`/content/${encodeURIComponent(form.id).replace(/%2F/g, "/")}`, {
    method: "PUT",
    body: JSON.stringify(toPayload(form))
  });
}

export async function deleteContent(id: string): Promise<void> {
  await request(`/content/${encodeURIComponent(id).replace(/%2F/g, "/")}`, {
    method: "DELETE"
  });
}

export async function gitStatus(): Promise<GitStatusResponse> {
  return request<GitStatusResponse>("/git/status");
}

export async function publish(message?: string): Promise<PublishResponse> {
  return request<PublishResponse>("/git/publish", {
    method: "POST",
    body: JSON.stringify({ message: message || undefined })
  });
}
