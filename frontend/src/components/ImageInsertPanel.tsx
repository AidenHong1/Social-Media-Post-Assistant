import { useState } from "react";
import { generateImage } from "../api";

interface ImageInsertPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onInsert: (url: string, caption: string) => void;
  variantId: number;
}

export function ImageInsertPanel({ isOpen, onClose, onInsert }: ImageInsertPanelProps) {
  const [activeTab, setActiveTab] = useState<"url" | "generate">("url");
  const [manualUrl, setManualUrl] = useState("");
  const [manualCaption, setManualCaption] = useState("");
  const [generatePrompt, setGeneratePrompt] = useState("");
  const [generateCaption, setGenerateCaption] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleManualInsert = () => {
    if (!manualUrl.trim()) {
      setError("请输入图片URL");
      return;
    }
    onInsert(manualUrl, manualCaption);
    setManualUrl("");
    setManualCaption("");
    setError(null);
  };

  const handleGenerate = async () => {
    if (!generatePrompt.trim()) {
      setError("请输入图片描述");
      return;
    }

    setIsGenerating(true);
    setError(null);
    try {
      const result = await generateImage(generatePrompt);
      onInsert(result.image_url, generateCaption || result.prompt_used);
      setGeneratePrompt("");
      setGenerateCaption("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成失败");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
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
        ) : (
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                图片描述（英文）
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
}
