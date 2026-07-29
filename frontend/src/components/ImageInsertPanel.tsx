import { useRef, useState } from "react";
import { createPortal } from "react-dom";
import { generateContextualImage, generateImage, uploadImage } from "../api";

const ACCEPTED_IMAGE_TYPES = "image/png,image/jpeg,image/gif,image/webp";
const MAX_UPLOAD_MB = 10;

export interface InsertedImageData {
  url: string;
  caption: string;
  filename?: string | null;
  promptUsed?: string | null;
  contextBefore?: string | null;
  contextAfter?: string | null;
  insertedBy: "manual" | "ai";
}

interface ImageInsertPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onInsert: (data: InsertedImageData) => void;
  variantId: number;
  contextBefore?: string;
  contextAfter?: string;
}

export function ImageInsertPanel({
  isOpen,
  onClose,
  onInsert,
  variantId,
  contextBefore = "",
  contextAfter = "",
}: ImageInsertPanelProps) {
  const [activeTab, setActiveTab] = useState<"url" | "upload" | "generate">("url");
  const [manualUrl, setManualUrl] = useState("");
  const [manualCaption, setManualCaption] = useState("");
  const [uploadCaption, setUploadCaption] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [generatePrompt, setGeneratePrompt] = useState("");
  const [generateCaption, setGenerateCaption] = useState("");
  const [useContext, setUseContext] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const hasContext = Boolean(contextBefore.trim() || contextAfter.trim());

  if (!isOpen) return null;

  const handleManualInsert = () => {
    if (!manualUrl.trim()) {
      setError("请输入图片URL");
      return;
    }
    onInsert({
      url: manualUrl,
      caption: manualCaption,
      insertedBy: "manual",
    });
    setManualUrl("");
    setManualCaption("");
    setError(null);
  };

  const handleFileSelected = async (file: File) => {
    const maxBytes = MAX_UPLOAD_MB * 1024 * 1024;
    if (file.size > maxBytes) {
      setError(`图片大小超过 ${MAX_UPLOAD_MB}MB 限制`);
      return;
    }

    setIsUploading(true);
    setError(null);
    try {
      const result = await uploadImage(file);
      onInsert({
        url: result.image_url,
        caption: uploadCaption,
        filename: result.filename,
        insertedBy: "manual",
      });
      setUploadCaption("");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败");
    } finally {
      setIsUploading(false);
    }
  };

  const handleGenerate = async () => {
    const useContextualMode = useContext && hasContext;

    if (!useContextualMode && !generatePrompt.trim()) {
      setError("请输入图片描述");
      return;
    }

    setIsGenerating(true);
    setError(null);
    try {
      if (useContextualMode) {
        const result = await generateContextualImage({
          variant_id: variantId,
          context_before: contextBefore,
          context_after: contextAfter,
          user_prompt: generatePrompt,
        });
        onInsert({
          url: result.image_url,
          caption: generateCaption || result.caption,
          filename: result.filename,
          promptUsed: result.prompt_used,
          contextBefore,
          contextAfter,
          insertedBy: "ai",
        });
      } else {
        const result = await generateImage(generatePrompt);
        onInsert({
          url: result.image_url,
          caption: generateCaption || result.prompt_used,
          filename: result.filename,
          promptUsed: result.prompt_used,
          insertedBy: "ai",
        });
      }
      setGeneratePrompt("");
      setGenerateCaption("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成失败");
    } finally {
      setIsGenerating(false);
    }
  };

  const modalContent = (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">插入图片</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab("url")}
            className={`flex-1 py-2 text-sm font-medium ${
              activeTab === "url"
                ? "border-b-2 border-blue-500 text-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            手动输入URL
          </button>
          <button
            onClick={() => setActiveTab("upload")}
            className={`flex-1 py-2 text-sm font-medium ${
              activeTab === "upload"
                ? "border-b-2 border-blue-500 text-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            本地上传
          </button>
          <button
            onClick={() => setActiveTab("generate")}
            className={`flex-1 py-2 text-sm font-medium ${
              activeTab === "generate"
                ? "border-b-2 border-blue-500 text-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            AI生成图片
          </button>
        </div>

        {error && (
          <div className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-md">
            {error}
          </div>
        )}

        {activeTab === "url" ? (
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                图片URL
              </label>
              <input
                type="text"
                value={manualUrl}
                onChange={(e) => setManualUrl(e.target.value)}
                placeholder="https://example.com/image.png"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                图片说明（可选）
              </label>
              <input
                type="text"
                value={manualCaption}
                onChange={(e) => setManualCaption(e.target.value)}
                placeholder="简短描述图片内容"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button
              onClick={handleManualInsert}
              className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              插入图片
            </button>
          </div>
        ) : activeTab === "upload" ? (
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                选择图片文件
              </label>
              <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPTED_IMAGE_TYPES}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    void handleFileSelected(file);
                  }
                }}
                disabled={isUploading}
                className="w-full text-sm text-gray-700 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:bg-blue-50 file:text-blue-600 file:text-sm file:font-medium hover:file:bg-blue-100 disabled:opacity-50"
              />
              <p className="mt-1 text-xs text-gray-500">
                支持 PNG / JPEG / GIF / WebP，最大 {MAX_UPLOAD_MB}MB
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                图片说明（可选）
              </label>
              <input
                type="text"
                value={uploadCaption}
                onChange={(e) => setUploadCaption(e.target.value)}
                placeholder="简短描述图片内容"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            {isUploading && (
              <p className="text-sm text-gray-500">正在上传...</p>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {hasContext && (
              <label className="flex items-start gap-2 text-sm text-gray-700 bg-blue-50 px-3 py-2 rounded-md">
                <input
                  type="checkbox"
                  checked={useContext}
                  onChange={(e) => setUseContext(e.target.checked)}
                  className="mt-0.5"
                />
                <span>
                  根据插入位置的上下文智能生成
                  <span className="block text-xs text-gray-500">
                    自动匹配该位置前后文字内容，下方描述将作为补充提示词
                  </span>
                </span>
              </label>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {useContext && hasContext ? "补充提示词（可选，英文）" : "图片描述（英文）"}
              </label>
              <textarea
                value={generatePrompt}
                onChange={(e) => setGeneratePrompt(e.target.value)}
                placeholder="Describe the image you want to generate..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                图片说明（可选）
              </label>
              <input
                type="text"
                value={generateCaption}
                onChange={(e) => setGenerateCaption(e.target.value)}
                placeholder="自定义说明，留空使用生成的描述"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="w-full py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg hover:from-blue-600 hover:to-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isGenerating ? "正在生成..." : "生成并插入"}
            </button>
          </div>
        )}
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
}
