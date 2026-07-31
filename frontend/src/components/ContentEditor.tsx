import { useEffect, useState } from "react";
import type { AutoMultiImageResponse, ContentSegment, ImageSegment } from "../types";
import { autoMultiImageForVariant, saveVariantContent } from "../api";
import { ImageInsertPanel, type InsertedImageData } from "./ImageInsertPanel";

interface ContentEditorProps {
  variantId: number;
  initialSegments: ContentSegment[];
  onSegmentsUpdate: (segments: ContentSegment[]) => void;
}

const CONTEXT_CHARS = 300;

export function ContentEditor({ variantId, initialSegments, onSegmentsUpdate }: ContentEditorProps) {
  const [segments, setSegments] = useState<ContentSegment[]>(initialSegments);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatingError, setGeneratingError] = useState<string | null>(null);
  const [insertPanelOpen, setInsertPanelOpen] = useState(false);
  const [insertAtIndex, setInsertAtIndex] = useState<number>(0);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  // 同步 segments 变化到父组件
  useEffect(() => {
    onSegmentsUpdate(segments);
  }, [segments, onSegmentsUpdate]);

  const getContextAround = (index: number) => {
    let before = "";
    for (let i = index - 1; i >= 0; i--) {
      const seg = segments[i];
      if (seg.type === "text") {
        before = seg.content;
        break;
      }
    }
    let after = "";
    for (let i = index; i < segments.length; i++) {
      const seg = segments[i];
      if (seg.type === "text") {
        after = seg.content;
        break;
      }
    }
    return {
      before: before.slice(-CONTEXT_CHARS),
      after: after.slice(0, CONTEXT_CHARS),
    };
  };

  const handleAutoImage = async () => {
    setIsGenerating(true);
    setGeneratingError(null);
    try {
      const result: AutoMultiImageResponse = await autoMultiImageForVariant(variantId, 3);

      // 从后往前插入，避免索引偏移（result.images 已按 insertion_index 升序排列）
      const newSegments = [...segments];
      for (let i = result.images.length - 1; i >= 0; i--) {
        const img = result.images[i];
        const imageSegment: ImageSegment = {
          type: "image",
          url: img.image_url,
          filename: img.filename,
          caption: img.caption,
          insertedBy: "ai",
          promptUsed: img.prompt_used,
        };

        // 插入到 segments[img.insertion_index] 之前
        newSegments.splice(img.insertion_index, 0, imageSegment);
      }

      setSegments(newSegments);
      setSaved(false);
    } catch (err) {
      setGeneratingError(err instanceof Error ? err.message : "生成配图失败");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleInsert = (data: InsertedImageData) => {
    const imageSegment: ImageSegment = {
      type: "image",
      url: data.url,
      filename: data.filename ?? null,
      caption: data.caption,
      insertedBy: data.insertedBy,
      promptUsed: data.promptUsed ?? null,
      contextBefore: data.contextBefore ?? null,
      contextAfter: data.contextAfter ?? null,
    };

    const newSegments = [...segments];
    newSegments.splice(insertAtIndex, 0, imageSegment);
    setSegments(newSegments);
    setInsertPanelOpen(false);
    setSaved(false);
  };

  const handleDeleteImage = (index: number) => {
    setSegments(segments.filter((_, i) => i !== index));
    setSaved(false);
  };

  const handleTextEdit = (index: number, newContent: string) => {
    const newSegments = [...segments];
    newSegments[index] = { type: "text", content: newContent };
    setSegments(newSegments);
    setSaved(false);
  };

  const openInsertPanel = (index: number) => {
    setInsertAtIndex(index);
    setInsertPanelOpen(true);
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveError(null);
    try {
      const res = await saveVariantContent(variantId, { segments });
      setSegments(res.segments);
      setSaved(true);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setIsSaving(false);
    }
  };

  const insertContext = getContextAround(insertAtIndex);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-200">
        <h4 className="text-sm font-semibold text-slate-800">图文内容编辑</h4>
        <div className="flex items-center gap-2">
          <button
            onClick={handleAutoImage}
            disabled={isGenerating}
            className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 px-3 py-1.5 text-xs font-medium text-white shadow-sm transition-all hover:from-blue-600 hover:to-purple-600 hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="text-sm">{isGenerating ? "⏳" : "✨"}</span>
            <span>{isGenerating ? "生成中..." : "AI自动配图"}</span>
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium shadow-sm transition-all ${
              saved
                ? "bg-emerald-500 text-white"
                : "bg-emerald-600 text-white hover:bg-emerald-700"
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            <span className="text-sm">{saved ? "✓" : "💾"}</span>
            <span>{isSaving ? "保存中..." : saved ? "已保存" : "保存排版"}</span>
          </button>
        </div>
      </div>

      {generatingError && (
        <div className="flex items-start gap-2 text-xs text-red-600 bg-red-50 px-3 py-2.5 rounded-lg border border-red-200">
          <span className="text-sm">⚠</span>
          <span>{generatingError}</span>
        </div>
      )}
      {saveError && (
        <div className="flex items-start gap-2 text-xs text-red-600 bg-red-50 px-3 py-2.5 rounded-lg border border-red-200">
          <span className="text-sm">⚠</span>
          <span>{saveError}</span>
        </div>
      )}

      <div className="space-y-3">
        {segments.map((segment, index) => (
          <div key={index} className="space-y-2">
            <InsertDivider onInsert={() => openInsertPanel(index)} />

            {segment.type === "text" ? (
              <textarea
                value={segment.content}
                onChange={(e) => handleTextEdit(index, e.target.value)}
                rows={Math.max(3, segment.content.split("\n").length)}
                className="w-full whitespace-pre-wrap break-words text-sm leading-relaxed text-gray-800 bg-gray-50 p-4 rounded-lg border border-gray-200 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent focus:bg-white transition-all"
              />
            ) : (
              <div className="relative bg-white border border-gray-200 rounded-lg p-4 space-y-3 shadow-sm">
                <img
                  src={segment.url}
                  alt={segment.caption ?? ""}
                  className="w-full rounded-lg shadow-sm"
                />
                {segment.caption && (
                  <p className="text-xs leading-relaxed text-gray-600 italic">{segment.caption}</p>
                )}
                <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                  <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium ${
                    segment.insertedBy === "ai"
                      ? "bg-purple-100 text-purple-700"
                      : "bg-gray-100 text-gray-700"
                  }`}>
                    <span className="text-sm">{segment.insertedBy === "ai" ? "✨" : "📎"}</span>
                    <span>{segment.insertedBy === "ai" ? "AI生成" : "手动插入"}</span>
                  </span>
                  <button
                    onClick={() => handleDeleteImage(index)}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium text-red-600 hover:bg-red-50 transition-colors"
                  >
                    <span className="text-sm">✕</span>
                    <span>删除</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}

        <InsertDivider onInsert={() => openInsertPanel(segments.length)} />
      </div>

      <ImageInsertPanel
        isOpen={insertPanelOpen}
        onClose={() => setInsertPanelOpen(false)}
        onInsert={handleInsert}
        variantId={variantId}
        contextBefore={insertContext.before}
        contextAfter={insertContext.after}
      />
    </div>
  );
}

function InsertDivider({ onInsert }: { onInsert: () => void }) {
  return (
    <div className="group relative h-3 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity duration-200">
      <div className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-blue-300 to-transparent"></div>
      <button
        onClick={onInsert}
        className="relative bg-white border-2 border-blue-400 rounded-full w-7 h-7 flex items-center justify-center text-blue-600 text-sm font-semibold hover:bg-blue-50 hover:border-blue-500 hover:shadow-md transition-all"
        title="在此位置插入图片"
      >
        +
      </button>
    </div>
  );
}

