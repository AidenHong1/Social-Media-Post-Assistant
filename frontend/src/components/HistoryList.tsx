import type { HistoryItem } from "../types";

interface Props {
  items: HistoryItem[];
  onSelect: (requestId: number) => void;
}

const PLATFORM_LABELS: Record<string, string> = {
  linkedin: "LinkedIn",
  facebook: "Facebook",
};

export default function HistoryList({ items, onSelect }: Props) {
  return (
    <div className="flex min-h-0 flex-1 flex-col rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-3 text-sm font-semibold text-slate-700">历史记录</h2>
      {items.length === 0 ? (
        <p className="text-xs text-slate-400">暂无历史记录</p>
      ) : (
        <ul className="min-h-0 space-y-1 overflow-y-auto xl:max-h-[calc(100vh-32rem)]">
          {items.map((item) => (
            <li key={item.request_id}>
              <button
                type="button"
                onClick={() => onSelect(item.request_id)}
                className="w-full rounded-md px-2 py-2 text-left text-sm hover:bg-slate-50"
              >
                <div className="truncate font-medium text-slate-700">{item.topic}</div>
                <div className="mt-0.5 flex items-center gap-2 text-xs text-slate-400">
                  <span>{new Date(item.created_at).toLocaleString()}</span>
                  <span>·</span>
                  <span>
                    {item.platforms.map((p) => PLATFORM_LABELS[p] ?? p).join(", ")}
                  </span>
                  <span>·</span>
                  <span>{item.variant_count} 条</span>
                </div>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
