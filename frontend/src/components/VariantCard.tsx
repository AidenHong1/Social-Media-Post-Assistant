import { useState } from "react";
import { rateVariant } from "../api";
import type { VariantOut } from "../types";
import { ContentEditor } from "./ContentEditor";
import RatingControl from "./RatingControl";

interface Props {
  variant: VariantOut;
  onRated: (variantId: number, score: number, isFavorite: boolean) => void;
}

export default function VariantCard({ variant, onRated }: Props) {
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showEditor, setShowEditor] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(variant.final_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  async function handleRate(score: number, isFavorite: boolean) {
    try {
      const result = await rateVariant(variant.id, { score, is_favorite: isFavorite });
      onRated(variant.id, result.score, result.is_favorite);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "评分失败");
    }
  }

  return (
    <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-slate-400">
          变体 {variant.variant_index + 1}
        </span>
        <div className="flex items-center gap-2">
          {variant.was_rewritten && (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-700">
              已重写优化
            </span>
          )}
          <button
            type="button"
            onClick={() => setShowEditor((v) => !v)}
            className={`rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors ${
              showEditor
                ? "bg-blue-100 text-blue-700"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            {showEditor ? "图文编辑中" : "图文排版"}
          </button>
        </div>
      </div>

      {showEditor ? (
        <ContentEditor
          variantId={variant.id}
          finalText={variant.final_text}
        />
      ) : (
        <pre className="whitespace-pre-wrap break-words rounded-lg bg-slate-50 p-3 font-sans text-sm text-slate-800">
          {variant.final_text}
        </pre>
      )}

      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={handleCopy}
          className="rounded-md border border-slate-300 px-3 py-1 text-xs text-slate-600 hover:bg-slate-50"
        >
          {copied ? "已复制" : "复制文案"}
        </button>
        <RatingControl
          score={variant.rating?.score ?? 0}
          isFavorite={variant.rating?.is_favorite ?? false}
          onRate={handleRate}
        />
      </div>

      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
