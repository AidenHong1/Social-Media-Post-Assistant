import type {
  AutoImageResponse,
  AutoMultiImageResponse,
  DocumentOut,
  GenerateContextualImageRequest,
  GenerateContextualImageResponse,
  GenerateRequest,
  GenerateResponse,
  HistoryItem,
  ImageGenerateResponse,
  ImageUploadResponse,
  LoginRequest,
  RateVariantRequest,
  RatingOut,
  SaveVariantContentRequest,
  Template,
  TemplateCreate,
  Token,
  UserOut,
  VariantContentResponse,
  VariantOut,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

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

export async function generateStream(
  req: GenerateRequest,
  onVariant: (variant: VariantOut) => void,
  onComplete: (data: { request_id: number; topic: string; brand_tone: string; created_at: string }) => void,
  onError: (error: string) => void,
): Promise<void> {
  const token = getToken();
  if (!token) {
    throw new Error("未授权，请重新登录");
  }

  const response = await fetch(`${BASE_URL}/generate-stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
    body: JSON.stringify(req),
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    throw new Error("Response body is not readable");
  }

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split("\n\n");

      for (const line of lines) {
        if (!line.trim() || !line.startsWith("data: ")) continue;

        const data = line.slice(6); // 移除 "data: " 前缀
        try {
          const event = JSON.parse(data);

          if (event.type === "variant") {
            onVariant(event.data);
          } else if (event.type === "complete") {
            onComplete(event.data);
          } else if (event.type === "error") {
            onError(event.message || "Unknown error");
          }
        } catch (e) {
          console.error("Failed to parse SSE event:", data, e);
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
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

// ─── Templates ────────────────────────────────────────────────────────────────

export async function getTemplates(): Promise<Template[]> {
  const res = await fetch(`${BASE_URL}/templates`, {
    headers: getHeaders(),
  });
  return handleResponse<Template[]>(res);
}

export async function createTemplate(req: TemplateCreate): Promise<Template> {
  const res = await fetch(`${BASE_URL}/templates`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(req),
  });
  return handleResponse<Template>(res);
}

export async function deleteTemplate(templateId: number): Promise<void> {
  const res = await fetch(`${BASE_URL}/templates/${templateId}`, {
    method: "DELETE",
    headers: getHeaders(),
  });
  if (res.status === 204) return;
  await handleResponse<void>(res);
}

// ─── Images ───────────────────────────────────────────────────────────────────

export async function generateImage(
  prompt: string,
  size = "1792x1024",
): Promise<ImageGenerateResponse> {
  const res = await fetch(`${BASE_URL}/images/generate`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ prompt, size }),
  });
  return handleResponse<ImageGenerateResponse>(res);
}

export async function autoImageForVariant(variantId: number): Promise<AutoImageResponse> {
  const res = await fetch(`${BASE_URL}/images/auto-for-variant`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ variant_id: variantId }),
  });
  return handleResponse<AutoImageResponse>(res);
}

export async function autoMultiImageForVariant(
  variantId: number,
  maxImages = 3,
): Promise<AutoMultiImageResponse> {
  const res = await fetch(`${BASE_URL}/images/auto-multi-for-variant`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ variant_id: variantId, max_images: maxImages }),
  });
  return handleResponse<AutoMultiImageResponse>(res);
}

export async function generateContextualImage(
  req: GenerateContextualImageRequest,
): Promise<GenerateContextualImageResponse> {
  const res = await fetch(`${BASE_URL}/images/generate-contextual`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(req),
  });
  return handleResponse<GenerateContextualImageResponse>(res);
}

export async function uploadImage(file: File): Promise<ImageUploadResponse> {
  const token = getToken();
  const headers: HeadersInit = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/images/upload`, {
    method: "POST",
    headers,
    body: formData,
  });
  return handleResponse<ImageUploadResponse>(res);
}

// ─── Variant content (图文排版持久化) ────────────────────────────────────────────

export async function getVariantContent(variantId: number): Promise<VariantContentResponse> {
  const res = await fetch(`${BASE_URL}/variants/${variantId}/content`, {
    headers: getHeaders(),
  });
  return handleResponse<VariantContentResponse>(res);
}

export async function saveVariantContent(
  variantId: number,
  req: SaveVariantContentRequest,
): Promise<VariantContentResponse> {
  const res = await fetch(`${BASE_URL}/variants/${variantId}/content`, {
    method: "PUT",
    headers: getHeaders(),
    body: JSON.stringify(req),
  });
  return handleResponse<VariantContentResponse>(res);
}
