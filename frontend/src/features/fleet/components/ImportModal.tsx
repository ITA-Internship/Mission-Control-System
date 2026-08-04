import { useState, useRef } from "react";
import { X, UploadCloud, File as FileIcon, AlertCircle, CheckCircle2, Loader } from "lucide-react";
import { importDronesCSV } from "../api/dronesApi";

interface ImportModalProps {
  onClose: () => void;
  // Можна додати колбек, щоб оновити таблицю після успішного імпорту
  onSuccess?: () => void;
}

interface ImportResult {
  added_count: number;
  errors: Array<{ row: number | string; error: string }>;
}

export function ImportModal({ onClose, onSuccess }: ImportModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setGlobalError(null);
    setResult(null);
    if (e.target.files && e.target.files.length > 0) {
      const selected = e.target.files[0];
      if (!selected.name.endsWith(".csv")) {
        setGlobalError("Please select a valid .csv file.");
        return;
      }
      setFile(selected);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setGlobalError(null);

    try {
      const data = await importDronesCSV(file);
      setResult({
        added_count: data.added_count || 0,
        errors: data.errors || [],
      });
      if (data.added_count > 0 && onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      setGlobalError(err.message || "An error occurred during import.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="flex max-h-[90vh] w-full max-w-md flex-col rounded-2xl border border-white/8 bg-[#161D26] shadow-2xl" onClick={(e) => e.stopPropagation()}>

        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/8 p-6 pb-4">
          <h2 className="text-[15px] font-semibold text-[#E6EAF0]">Import Drones CSV</h2>
          <button onClick={onClose} className="rounded p-1 text-[#8A94A6] transition-colors hover:bg-white/5 hover:text-[#E6EAF0]">
            <X size={16} />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto p-6">
          {!result ? (
            <div className="flex flex-col gap-4">
              {/* Зона вибору файлу */}
              <div
                className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-colors ${
                  file ? "border-[#C8A24A]/50 bg-[#C8A24A]/5" : "border-white/10 bg-white/3 hover:border-[#C8A24A]/30 hover:bg-white/5"
                }`}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  type="file"
                  accept=".csv"
                  className="hidden"
                  ref={fileInputRef}
                  onChange={handleFileSelect}
                />

                {file ? (
                  <>
                    <FileIcon size={32} className="mb-3 text-[#C8A24A]" />
                    <p className="text-[13px] font-medium text-[#E6EAF0]">{file.name}</p>
                    <p className="mt-1 text-[11px] text-[#8A94A6]">
                      {(file.size / 1024).toFixed(2)} KB
                    </p>
                  </>
                ) : (
                  <>
                    <UploadCloud size={32} className="mb-3 text-[#8A94A6]" />
                    <p className="text-[13px] font-medium text-[#E6EAF0]">Click to select a CSV file</p>
                    <p className="mt-1 text-[11px] text-[#8A94A6]">.csv files only (Max 10MB)</p>
                  </>
                )}
              </div>

              {globalError && (
                <div className="flex items-start gap-2 rounded-lg border border-[#E5484D]/30 bg-[#E5484D]/10 p-3 text-[#E5484D]">
                  <AlertCircle size={14} className="mt-0.5 shrink-0" />
                  <p className="text-[12px]">{globalError}</p>
                </div>
              )}

              <button
                onClick={handleUpload}
                disabled={!file || isUploading}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#C8A24A] py-2.5 text-[13px] font-semibold text-[#0B0F14] transition-colors hover:bg-[#d4ae5c] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isUploading ? <Loader size={14} className="animate-spin" /> : <UploadCloud size={14} />}
                {isUploading ? "Uploading..." : "Import File"}
              </button>
            </div>
          ) : (
            /* Результати імпорту */
            <div className="flex flex-col gap-4">
              <div className="flex flex-col items-center justify-center rounded-xl bg-white/3 p-6 text-center">
                <CheckCircle2 size={40} className="mb-3 text-[#30A46C]" />
                <h3 className="text-[15px] font-medium text-[#E6EAF0]">Import Completed</h3>
                <p className="mt-1 text-[13px] text-[#8A94A6]">
                  Successfully added <span className="font-semibold text-[#30A46C]">{result.added_count}</span> drones.
                </p>
              </div>

              {result.errors.length > 0 && (
                <div className="flex flex-col gap-2">
                  <h4 className="text-[12px] font-semibold uppercase tracking-wider text-[#8A94A6]">
                    Row Errors ({result.errors.length})
                  </h4>
                  <div className="max-h-[200px] overflow-y-auto rounded-lg border border-white/10 bg-[#0F1620] p-2">
                    {result.errors.map((err, idx) => (
                      <div key={idx} className="flex gap-3 border-b border-white/5 p-2 last:border-0">
                        <span className="shrink-0 text-[12px] font-mono text-[#8A94A6]">Row {err.row}</span>
                        <span className="text-[12px] text-[#E5484D]">{err.error}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <button
                onClick={onClose}
                className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 py-2.5 text-[13px] font-medium text-[#E6EAF0] transition-colors hover:bg-white/10"
              >
                Close
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}