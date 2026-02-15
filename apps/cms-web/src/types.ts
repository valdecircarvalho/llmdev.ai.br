export type ContentType = "note" | "post";

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface ContentSummary {
  id: string;
  type: ContentType;
  path: string;
  slug: string;
  title: string;
  date?: string;
  draft?: boolean;
  updated_at: string;
}

export interface ContentListResponse {
  items: ContentSummary[];
  page: number;
  page_size: number;
  total: number;
}

export interface ContentDocument {
  id: string;
  type: ContentType;
  path: string;
  frontmatter: Record<string, unknown>;
  body: string;
  raw: string;
}

export interface GitStatusItem {
  status: string;
  path: string;
}

export interface GitStatusResponse {
  changed: boolean;
  files: GitStatusItem[];
}

export interface PublishResponse {
  commit_hash: string;
  message: string;
  files: GitStatusItem[];
  output: string;
}

export interface EditorFormState {
  id?: string;
  type: ContentType;
  title: string;
  date: string;
  categories: string;
  draft: boolean;
  link: string;
  comment: string;
  body: string;
}
