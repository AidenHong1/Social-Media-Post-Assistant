import type {
  DocumentOut,
  GenerateRequest,
  GenerateResponse,
  HistoryItem,
  LoginRequest,
  RateVariantRequest,
  RatingOut,
  Token,
  UserOut,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

// Token管理
const TOKEN_KEY = "auth_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (res.status === 401) {
    removeToken();
    window.location.href = "/";
    throw new Error("未授权，请重新登录");
  }
  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // ignore parse failure, use default detail
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

function getHeaders(): HeadersInit {
  const headers: HeadersInit = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export async function login(req: LoginRequest): Promise<Token> {
  const formData = new URLSearchParams();
  formData.append("username", req.username);
  formData.append("password", req.password);

  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData,
  });
  return handleResponse<Token>(res);
}

export async function getCurrentUser(): Promise<UserOut> {
  const res = await fetch(`${BASE_URL}/auth/me`, {
    headers: getHeaders(),
  });
  return handleResponse<UserOut>(res);
}

export async function generate(req: GenerateRequest): Promise<GenerateResponse> {
  const res = await fetch(`${BASE_URL}/generate`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(req),
  });
  return handleResponse<GenerateResponse>(res);
}

export async function getHistory(): Promise<HistoryItem[]> {
  const res = await fetch(`${BASE_URL}/history`, {
    headers: getHeaders(),
  });
  return handleResponse<HistoryItem[]>(res);
}

export async function getHistoryItem(id: number): Promise<GenerateResponse> {
  const res = await fetch(`${BASE_URL}/history/${id}`, {
    headers: getHeaders(),
  });
  return handleResponse<GenerateResponse>(res);
}

export async function rateVariant(
  variantId: number,
  body: RateVariantRequest,
): Promise<RatingOut> {
  const res = await fetch(`${BASE_URL}/variants/${variantId}/rate`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(body),
  });
  return handleResponse<RatingOut>(res);
}

export async function getDocuments(): Promise<DocumentOut[]> {
  const res = await fetch(`${BASE_URL}/documents`, {
    headers: getHeaders(),
  });
  return handleResponse<DocumentOut[]>(res);
}

export async function uploadDocument(file: File): Promise<DocumentOut> {
  const token = getToken();
  const headers: HeadersInit = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/documents/upload`, {
    method: "POST",
    headers,
    body: formData,
  });
  return handleResponse<DocumentOut>(res);
}

export async function replaceDocument(documentId: number, file: File): Promise<DocumentOut> {
  const token = getToken();
  const headers: HeadersInit = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/documents/${documentId}`, {
    method: "PUT",
    headers,
    body: formData,
  });
  return handleResponse<DocumentOut>(res);
}

export async function deleteDocument(documentId: number): Promise<void> {
  const res = await fetch(`${BASE_URL}/documents/${documentId}`, {
    method: "DELETE",
    headers: getHeaders(),
  });
  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // ignore parse failure, use default detail
    }
    throw new Error(detail);
  }
}
