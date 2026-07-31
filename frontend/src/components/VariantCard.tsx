import { useEffect, useState } from "react";
import { getVariantContent, rateVariant } from "../api";
import type { ContentSegment, VariantOut } from "../types";
import { ContentEditor } from "./ContentEditor";
import PlatformPostCard from "./PlatformPostCard";
import RatingControl from "./RatingControl";

interface Props {
  variant: VariantOut;
  onRated: (variantId: number, score: number, isFavorite: boolean) => void;
}

export default function VariantCard({ variant, onRated }: Props) {
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [segments, setSegments] = useState<ContentSegment[]>([]);
  const [isLoadingSegments, setIsLoadingSegments] = useState(true);

  // 始终加载 segments（包含图片），无论是否在编辑模式
  useEffect(() => {
    let cancelled = false;
    setIsLoadingSegments(true);
    getVariantContent(variant.id)
      .then((res) => {
        if (!cancelled && res.segments.length > 0) {
          setSegments(res.segments);
        } else if (!cancelled) {
          // 后端返回空，按段落拆分 final_text 作为初始 segments
          const paragraphs = variant.final_text.split(/\n\n+/).filter(p => p.trim() !== "");
          setSegments(
            paragraphs.length > 0
              ? paragraphs.map(p => ({ type: "text", content: p }))
              : [{ type: "text", content: variant.final_text }]
          );
        }
      })
      .catch(() => {
        if (!cancelled) {
          const paragraphs = variant.final_text.split(/\n\n+/).filter(p => p.trim() !== "");
          setSegments(
            paragraphs.length > 0
              ? paragraphs.map(p => ({ type: "text", content: p }))
              : [{ type: "text", content: variant.final_text }]
          );
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoadingSegments(false);
      });
    return () => {
      cancelled = true;
    };
  }, [variant.id, variant.final_text]);

  async function handleCopy() {
    const textOnly = segments
      .filter(s => s.type === "text")
      .map(s => s.content)
      .join("\n\n");
    await navigator.clipboard.writeText(textOnly);
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
    <div className={editMode ? "space-y-4 rounded-xl border-2 border-blue-400 bg-blue-50/30 p-5 shadow-sm" : "space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm"}>
      <div className="flex items-center justify-between">
        <span className="inline-flex items-center gap-1.5 rounded-md bg-slate-100 px-2.5 py-1 text-xs font-semibold uppercase tracking-wider text-slate-600">
          <span className="text-sm">✦</span>
          变体 {variant.variant_index + 1}
        </span>
        <div className="flex items-center gap-2">
          {variant.was_rewritten && (
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-700">
              <span>✓</span>
              已优化
            </span>
          )}
          <button
            type="button"
            onClick={() => setEditMode((v) => !v)}
            className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all shadow-sm ${
              editMode
                ? "bg-blue-600 text-white hover:bg-blue-700 shadow-blue-200"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-300"
            }`}
          >
            <span className="text-sm">{editMode ? "✕" : "✎"}</span>
            <span>{editMode ? "关闭编辑" : "图文排版"}</span>
          </button>
        </div>
      </div>

      {isLoadingSegments ? (
        <p className="text-sm text-gray-500">加载内容中...</p>
      ) : editMode ? (
        <ContentEditor
          variantId={variant.id}
          initialSegments={segments}
          onSegmentsUpdate={setSegments}
        />
      ) : (
        <PlatformPostCard platform={variant.platform} segments={segments} />
      )}

      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={handleCopy}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm transition-all hover:bg-slate-50 hover:border-slate-400"
        >
          <span className="text-sm">{copied ? "✓" : "⎘"}</span>
          <span>{copied ? "已复制" : "复制文案"}</span>
        </button>
        <RatingControl
          score={variant.rating?.score ?? 0}
          isFavorite={variant.rating?.is_favorite ?? false}
          onRate={handleRate}
        />
      </div>

      {error && <p className="text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>}
    </div>
  );
}
