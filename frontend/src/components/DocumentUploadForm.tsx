import { useRef, useState } from "react";

interface Props {
  isUploading: boolean;
  onUpload: (file: File) => void;
}

const ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".txt"];

export default function DocumentUploadForm({ isUploading, onUpload }: Props) {
  const [validationError, setValidationError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      setValidationError("仅支持 PDF、DOCX、TXT 格式");
      if (inputRef.current) inputRef.current.value = "";
      return;
    }

    setValidationError(null);
    onUpload(file);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div className="space-y-2 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-800">上传企业文档</h2>
      <p className="text-xs text-slate-500">
        支持 PDF / DOCX / TXT，内容将用于生成文案时提供事实依据
      </p>

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXTENSIONS.join(",")}
        disabled={isUploading}
        onChange={handleFileChange}
        className="block w-full text-sm text-slate-700 file:mr-3 file:rounded-md file:border-0 file:bg-blue-600 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white file:hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      />

      {isUploading && <p className="text-sm text-slate-500">上传中，正在解析并生成向量索引...</p>}
      {validationError && <p className="text-sm text-red-600">{validationError}</p>}
    </div>
  );
}
