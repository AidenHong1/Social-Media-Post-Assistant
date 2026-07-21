import { useCallback, useEffect, useState } from "react";
import { deleteDocument, getDocuments, replaceDocument, uploadDocument } from "../api";
import type { DocumentOut } from "../types";
import DocumentList from "./DocumentList";
import DocumentUploadForm from "./DocumentUploadForm";

export default function KnowledgeManager() {
  const [documents, setDocuments] = useState<DocumentOut[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [replacingId, setReplacingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const items = await getDocuments();
      setDocuments(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载文档列表失败");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleUpload(file: File) {
    setIsUploading(true);
    setError(null);
    try {
      await uploadDocument(file);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败，请稍后重试");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleReplace(documentId: number, file: File) {
    setReplacingId(documentId);
    setError(null);
    try {
      await replaceDocument(documentId, file);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新失败，请稍后重试");
    } finally {
      setReplacingId(null);
    }
  }

  async function handleDelete(documentId: number) {
    setError(null);
    try {
      await deleteDocument(documentId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败，请稍后重试");
    }
  }

  return (
    <main className="mx-auto grid w-full max-w-[1600px] gap-6 px-4 py-6 sm:px-6 xl:grid-cols-[minmax(320px,420px)_minmax(0,1fr)] 2xl:grid-cols-[minmax(340px,440px)_minmax(0,1fr)]">
      <div className="space-y-6 xl:sticky xl:top-6 xl:self-start">
        <DocumentUploadForm isUploading={isUploading} onUpload={handleUpload} />
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>
      <div className="min-w-0">
        <DocumentList
          documents={documents}
          replacingId={replacingId}
          onReplace={handleReplace}
          onDelete={handleDelete}
        />
      </div>
    </main>
  );
}
