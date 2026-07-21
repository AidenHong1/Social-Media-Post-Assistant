import type { GenerateResponse, VariantOut } from "../types";
import VariantCard from "./VariantCard";

interface Props {
  result: GenerateResponse | null;
  isLoading: boolean;
  error: string | null;
  onRated: (variantId: number, score: number, isFavorite: boolean) => void;
}

const PLATFORM_LABELS: Record<string, string> = {
  linkedin: "LinkedIn",
  facebook: "Facebook",
};

function groupByPlatform(variants: VariantOut[]): Record<string, VariantOut[]> {
  const groups: Record<string, VariantOut[]> = {};
  for (const v of variants) {
    if (!groups[v.platform]) groups[v.platform] = [];
    groups[v.platform].push(v);
  }
  return groups;
}

export default function ResultsView({ result, isLoading, error, onRated }: Props) {
  if (isLoading) {
    return (
      <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-5 shadow-sm xl:min-h-[calc(100vh-10rem)]">
        <p className="text-sm text-slate-500">正在生成文案，请稍候（可能需要几十秒）...</p>
        <div className="h-24 animate-pulse rounded-md bg-slate-100" />
        <div className="h-24 animate-pulse rounded-md bg-slate-100" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-5 text-sm text-red-700 xl:min-h-[calc(100vh-10rem)]">
        生成失败：{error}
      </div>
    );
  }

  if (!result) {
    return (
      <div className="flex min-h-[320px] items-center justify-center rounded-lg border border-dashed border-slate-300 p-5 text-center text-sm text-slate-400 xl:min-h-[calc(100vh-10rem)]">
        填写左侧表单并点击"生成文案"开始
      </div>
    );
  }

  const grouped = groupByPlatform(result.variants);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-800">{result.topic}</h2>
        <p className="text-xs text-slate-400">
          {new Date(result.created_at).toLocaleString()}
        </p>
      </div>

      {Object.entries(grouped).map(([platform, variants]) => (
        <div key={platform} className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-600">
            {PLATFORM_LABELS[platform] ?? platform}
          </h3>
          <div className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-3">
            {variants.map((v) => (
              <VariantCard key={v.id} variant={v} onRated={onRated} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
