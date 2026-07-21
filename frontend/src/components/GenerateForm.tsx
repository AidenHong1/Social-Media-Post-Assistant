import { useState } from "react";
import type { GenerateRequest, PlatformName } from "../types";

interface Props {
  isLoading: boolean;
  onSubmit: (req: GenerateRequest) => void;
}

const PLATFORM_OPTIONS: { value: PlatformName; label: string }[] = [
  { value: "linkedin", label: "LinkedIn" },
  { value: "facebook", label: "Facebook" },
];

export default function GenerateForm({ isLoading, onSubmit }: Props) {
  const [topic, setTopic] = useState("");
  const [keyPointsText, setKeyPointsText] = useState("");
  const [brandTone, setBrandTone] = useState("");
  const [platforms, setPlatforms] = useState<PlatformName[]>(["linkedin", "facebook"]);
  const [nVariants, setNVariants] = useState(2);
  const [validationError, setValidationError] = useState<string | null>(null);

  function togglePlatform(value: PlatformName) {
    setPlatforms((prev) =>
      prev.includes(value) ? prev.filter((p) => p !== value) : [...prev, value],
    );
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!topic.trim()) {
      setValidationError("请填写主题");
      return;
    }
    if (platforms.length === 0) {
      setValidationError("请至少选择一个平台");
      return;
    }
    setValidationError(null);

    const key_points = keyPointsText
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.length > 0);

    onSubmit({
      topic: topic.trim(),
      key_points,
      brand_tone: brandTone.trim(),
      platforms,
      n_variants: nVariants,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-800">生成新文案</h2>

      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700">主题</label>
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="例如：发布全新数据分析仪表盘"
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700">关键要点（每行一条）</label>
        <textarea
          value={keyPointsText}
          onChange={(e) => setKeyPointsText(e.target.value)}
          rows={4}
          placeholder={"实时数据指标\n无需代码即可配置"}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700">品牌语气（可选）</label>
        <input
          type="text"
          value={brandTone}
          onChange={(e) => setBrandTone(e.target.value)}
          placeholder="例如：自信但平易近人"
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
      </div>

      <div>
        <span className="mb-1 block text-sm font-medium text-slate-700">目标平台</span>
        <div className="flex gap-4">
          {PLATFORM_OPTIONS.map((opt) => (
            <label key={opt.value} className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={platforms.includes(opt.value)}
                onChange={() => togglePlatform(opt.value)}
              />
              {opt.label}
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700">每平台变体数量</label>
        <select
          value={nVariants}
          onChange={(e) => setNVariants(Number(e.target.value))}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        >
          <option value={1}>1</option>
          <option value={2}>2</option>
          <option value={3}>3</option>
        </select>
      </div>

      {validationError && <p className="text-sm text-red-600">{validationError}</p>}

      <button
        type="submit"
        disabled={isLoading}
        className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isLoading ? "生成中..." : "生成文案"}
      </button>
    </form>
  );
}
