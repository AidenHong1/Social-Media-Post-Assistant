export type PlatformName = "linkedin" | "facebook";

export interface LoginRequest {
  username: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface UserOut {
  id: number;
  username: string;
  full_name: string | null;
  is_active: boolean;
}

export interface GenerateRequest {
  topic: string;
  key_points: string[];
  brand_tone: string;
  platforms: PlatformName[];
  n_variants: number;
}

export interface RatingOut {
  score: number;
  is_favorite: boolean;
}

export interface VariantOut {
  id: number;
  platform: string;
  variant_index: number;
  final_text: string;
  draft_text: string;
  critique_feedback: string | null;
  was_rewritten: boolean;
  rating: RatingOut | null;
}

export interface GenerateResponse {
  request_id: number;
  topic: string;
  brand_tone: string;
  created_at: string;
  variants: VariantOut[];
}

export interface HistoryItem {
  request_id: number;
  topic: string;
  platforms: string[];
  created_at: string;
  variant_count: number;
}

export interface RateVariantRequest {
  score: number;
  is_favorite: boolean;
}

export type DocumentStatus = "processing" | "ready" | "failed";

export interface DocumentOut {
  id: number;
  filename: string;
  file_type: string;
  status: DocumentStatus;
  chunk_count: number;
  error_message: string | null;
  uploaded_at: string;
  updated_at: string;
}
