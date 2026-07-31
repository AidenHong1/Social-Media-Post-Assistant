import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import type { Template } from "../types";
import { getTemplates } from "../api";

interface TemplateLibraryProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (template: Template) => void;
}

const CATEGORY_LABELS: Record<string, string> = {
  all: "全部",
  product_launch: "产品发布",
  thought_leadership: "思想领导力",
  career_milestone: "职业成就",
  event: "活动预告",
  social_proof: "成功案例",
  behind_scenes: "幕后故事",
  engagement: "社区互动",
  year_review: "年度总结",
};

const PLATFORM_LABELS: Record<string, string> = {
  linkedin: "LinkedIn",
  facebook: "Facebook",
  both: "两个平台",
};

export function TemplateLibrary({ isOpen, onClose, onSelect }: TemplateLibraryProps) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [platformFilter, setPlatformFilter] = useState("all");

  useEffect(() => {
    if (!isOpen) return;
    setIsLoading(true);
    setError(null);
    getTemplates()
      .then(setTemplates)
      .catch((err) => setError(err instanceof Error ? err.message : "加载失败"))
      .finally(() => setIsLoading(false));
  }, [isOpen]);

  if (!isOpen) return null;

  const categories = [
    "all",
    ...Array.from(new Set(templates.map((t) => t.category))),
  ];

  const filtered = templates.filter((t) => {
    const catMatch = categoryFilter === "all" || t.category === categoryFilter;
    const platMatch =
      platformFilter === "all" || t.platform === platformFilter || t.platform === "both";
    return catMatch && platMatch;
  });

  return createPortal(
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">选择内容模板</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">
            ✕
          </button>
        </div>

        <div className="px-6 py-3 border-b border-gray-100 space-y-2">
          <div className="flex flex-wrap gap-2">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setCategoryFilter(cat)}
                className={`px-3 py-1 text-sm rounded-full transition-colors ${
                  categoryFilter === cat
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {CATEGORY_LABELS[cat] ?? cat}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            {["all", "linkedin", "facebook"].map((plat) => (
              <button
                key={plat}
                onClick={() => setPlatformFilter(plat)}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  platformFilter === plat
                    ? "bg-indigo-600 text-white"
                    : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                }`}
              >
                {plat === "all" ? "所有平台" : PLATFORM_LABELS[plat]}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {isLoading && (
            <div className="flex items-center justify-center py-12 text-gray-400">
              加载中...
            </div>
          )}
          {error && (
            <div className="text-sm text-red-600 bg-red-50 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}
          {!isLoading && !error && filtered.length === 0 && (
            <div className="text-center py-12 text-gray-400 text-sm">无匹配模板</div>
          )}
          {!isLoading && !error && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {filtered.map((t) => (
                <button
                  key={t.id}
                  onClick={() => {
                    onSelect(t);
                    onClose();
                  }}
                  className="text-left p-4 border border-gray-200 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-all group"
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="font-medium text-gray-900 group-hover:text-blue-700">
                      {t.name}
                    </span>
                    <span className={`flex-shrink-0 text-xs px-2 py-0.5 rounded-full ${
                      t.platform === "linkedin"
                        ? "bg-blue-100 text-blue-700"
                        : t.platform === "facebook"
                        ? "bg-indigo-100 text-indigo-700"
                        : "bg-gray-100 text-gray-600"
                    }`}>
                      {PLATFORM_LABELS[t.platform] ?? t.platform}
                    </span>
                  </div>
                  {t.description && (
                    <p className="text-xs text-gray-500 mb-2">{t.description}</p>
                  )}
                  {t.brand_tone && (
                    <p className="text-xs text-gray-400">语气：{t.brand_tone}</p>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}
