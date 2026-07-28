import { useState } from "react";
import type { AutoImageResponse, ContentSegment, ImageSegment, TextSegment } from "../types";
import { autoImageForVariant } from "../api";
import { ImageInsertPanel } from "./ImageInsertPanel";

interface ContentEditorProps {
  variantId: number;
  finalText: string;
}

export function ContentEditor({ variantId, finalText }: ContentEditorProps) {
  const [segments, setSegments] = useState<ContentSegment[]>([
    { type: "text", content: finalText },
  ]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatingError, setGeneratingError] = useState<string | null>(null);
  const [insertPanelOpen, setInsertPanelOpen] = useState(false);
  const [insertAtIndex, setInsertAtIndex] = useState<number>(0);

  const handleAutoImage = async () => {
    setIsGenerating(true);
    setGeneratingError(null);
    try {
      const result: AutoImageResponse = await autoImageForVariant(variantId);

      const imageSegment: ImageSegment = {
        type: "image",
        url: result.image_url,
        caption: result.caption,
        insertedBy: "ai",
      };

      const newSegments = insertImageAtPosition(
        segments,
        imageSegment,
        result.insertion_position
      );
      setSegments(newSegments);
    } catch (err) {
      setGeneratingError(err instanceof Error ? err.message : "生成配图失败");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleManualInsert = (url: string, caption: string) => {
    const imageSegment: ImageSegment = {
      type: "image",
      url,
      caption,
      insertedBy: "manual",
    };

    const newSegments = [...segments];
    newSegments.splice(insertAtIndex, 0, imageSegment);
    setSegments(newSegments);
    setInsertPanelOpen(false);
  };

  const handleDeleteImage = (index: number) => {
    setSegments(segments.filter((_, i) => i !== index));
  };

  const openInsertPanel = (index: number) => {
    setInsertAtIndex(index);
    setInsertPanelOpen(true);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-gray-700">内容预览</h4>
        <button
          onClick={handleAutoImage}
          disabled={isGenerating}
          className="px-3 py-1.5 text-sm bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg hover:from-blue-600 hover:to-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {isGenerating ? "正在生成配图..." : "AI自动配图"}
        </button>
      </div>

      {generatingError && (
        <div className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-md">
          {generatingError}
        </div>
      )}

      <div className="space-y-2">
        {segments.map((segment, index) => (
          <div key={index}>
            <InsertDivider onInsert={() => openInsertPanel(index)} />

            {segment.type === "text" ? (
              <pre className="whitespace-pre-wrap break-words text-sm text-gray-800 bg-gray-50 p-3 rounded-lg">
                {segment.content}
              </pre>
            ) : (
              <div className="relative bg-white border border-gray-200 rounded-lg p-3 space-y-2">
                <img
                  src={segment.url}
                  alt={segment.caption}
                  className="w-full rounded-md"
                />
                <p className="text-xs text-gray-600">{segment.caption}</p>
                <div className="flex items-center justify-between text-xs">
                  <span className={`px-2 py-0.5 rounded ${
                    segment.insertedBy === "ai"
                      ? "bg-purple-100 text-purple-700"
                      : "bg-gray-100 text-gray-700"
                  }`}>
                    {segment.insertedBy === "ai" ? "AI生成" : "手动插入"}
                  </span>
                  <button
                    onClick={() => handleDeleteImage(index)}
                    className="text-red-600 hover:text-red-800"
                  >
                    删除
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
        onInsert={handleManualInsert}
        variantId={variantId}
      />
    </div>
  );
}

function InsertDivider({ onInsert }: { onInsert: () => void }) {
  return (
    <div className="group relative h-2 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
      <div className="absolute inset-x-0 h-px bg-gray-300"></div>
      <button
        onClick={onInsert}
        className="relative bg-white border border-gray-300 rounded-full w-6 h-6 flex items-center justify-center text-gray-600 hover:bg-gray-50 hover:text-gray-800 hover:border-gray-400"
      >
        +
      </button>
    </div>
  );
}

function insertImageAtPosition(
  segments: ContentSegment[],
  imageSegment: ImageSegment,
  position: string
): ContentSegment[] {
  const textIdx = segments.findIndex(s => s.type === "text");

  if (textIdx === -1) {
    return position === "beginning" ? [imageSegment, ...segments] : [...segments, imageSegment];
  }

  const textSeg = segments[textIdx] as TextSegment;
  const paragraphs = textSeg.content.split(/\n\n+/);

  let splitIndex = 0;
  switch (position) {
    case "beginning":
      return [imageSegment, ...segments];
    case "after_hook":
      splitIndex = Math.min(1, paragraphs.length - 1);
      break;
    case "before_cta":
      splitIndex = Math.max(paragraphs.length - 1, 1);
      break;
    case "end":
    default:
      return [...segments, imageSegment];
  }

  const before = paragraphs.slice(0, splitIndex).join("\n\n");
  const after = paragraphs.slice(splitIndex).join("\n\n");

  const newSegments = [...segments];
  const replacement: ContentSegment[] = [];
  if (before) replacement.push({ type: "text", content: before });
  replacement.push(imageSegment);
  if (after) replacement.push({ type: "text", content: after });

  newSegments.splice(textIdx, 1, ...replacement);
  return newSegments;
}
