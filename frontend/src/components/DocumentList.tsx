import { useRef } from "react";
import type { DocumentOut } from "../types";

interface Props {
  documents: DocumentOut[];
  replacingId: number | null;
  onReplace: (documentId: number, file: File) => void;
  onDelete: (documentId: number) => void;
}

const STATUS_LABELS: Record<string, string> = {
  processing: "处理中",
  ready: "已就绪",
  failed: "失败",
};

const STATUS_STYLES: Record<string, string> = {
  processing: "bg-amber-100 text-amber-700",
  ready: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

export default function DocumentList({ documents, replacingId, onReplace, onDelete }: Props) {
  const fileInputsRef = useRef<Record<number, HTMLInputElement | null>>({});

  function triggerReplace(documentId: number) {
    fileInputsRef.current[documentId]?.click();
  }

  function handleReplaceFileChange(documentId: number, e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) onReplace(documentId, file);
    e.target.value = "";
  }

  function handleDelete(documentId: number, filename: string) {
    if (window.confirm(`确定删除文档「${filename}」吗？该操作不可撤销。`)) {
      onDelete(documentId);
    }
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="mb-3 text-lg font-semibold text-slate-800">已上传文档</h2>

      {documents.length === 0 ? (
        <p className="text-sm text-slate-400">暂无文档，上传企业资料以增强生成内容的事实依据</p>
      ) : (
        <ul className="space-y-2">
          {documents.map((doc) => (
            <li
              key={doc.id}
              className="flex items-center justify-between gap-3 rounded-md border border-slate-100 px-3 py-2"
            >
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium text-slate-700">{doc.filename}</div>
                <div className="mt-0.5 flex items-center gap-2 text-xs text-slate-400">
                  <span
                    className={`rounded-full px-2 py-0.5 font-medium ${STATUS_STYLES[doc.status] ?? "bg-slate-100 text-slate-600"}`}
                  >
                    {STATUS_LABELS[doc.status] ?? doc.status}
                  </span>
                  <span>{doc.chunk_count} 个片段</span>
                  <span>·</span>
                  <span>{new Date(doc.updated_at).toLocaleString()}</span>
                </div>
                {doc.status === "failed" && doc.error_message && (
                  <p className="mt-1 truncate text-xs text-red-600" title={doc.error_message}>
                    {doc.error_message}
                  </p>
                )}
              </div>

              <div className="flex shrink-0 items-center gap-2">
                <input
                  ref={(el) => {
                    fileInputsRef.current[doc.id] = el;
                  }}
                  type="file"
                  accept=".pdf,.docx,.txt"
                  className="hidden"
                  onChange={(e) => handleReplaceFileChange(doc.id, e)}
                />
                <button
                  type="button"
                  disabled={replacingId === doc.id}
                  onClick={() => triggerReplace(doc.id)}
                  className="rounded-md border border-slate-300 px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {replacingId === doc.id ? "更新中..." : "更新"}
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(doc.id, doc.filename)}
                  className="rounded-md border border-red-200 px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50"
                >
                  删除
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
