import type {
  DocumentOut,
  GenerateRequest,
  GenerateResponse,
  HistoryItem,
  RateVariantRequest,
  RatingOut,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

async function handleResponse<T>(res: Response): Promise<T> {
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

export async function generate(req: GenerateRequest): Promise<GenerateResponse> {
  const res = await fetch(`${BASE_URL}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  return handleResponse<GenerateResponse>(res);
}

export async function getHistory(): Promise<HistoryItem[]> {
  const res = await fetch(`${BASE_URL}/history`);
  return handleResponse<HistoryItem[]>(res);
}

export async function getHistoryItem(id: number): Promise<GenerateResponse> {
  const res = await fetch(`${BASE_URL}/history/${id}`);
  return handleResponse<GenerateResponse>(res);
}

export async function rateVariant(
  variantId: number,
  body: RateVariantRequest,
): Promise<RatingOut> {
  const res = await fetch(`${BASE_URL}/variants/${variantId}/rate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse<RatingOut>(res);
}

export async function getDocuments(): Promise<DocumentOut[]> {
  const res = await fetch(`${BASE_URL}/documents`);
  return handleResponse<DocumentOut[]>(res);
}

export async function uploadDocument(file: File): Promise<DocumentOut> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/documents/upload`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<DocumentOut>(res);
}

export async function replaceDocument(documentId: number, file: File): Promise<DocumentOut> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/documents/${documentId}`, {
    method: "PUT",
    body: formData,
  });
  return handleResponse<DocumentOut>(res);
}

export async function deleteDocument(documentId: number): Promise<void> {
  const res = await fetch(`${BASE_URL}/documents/${documentId}`, {
    method: "DELETE",
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
