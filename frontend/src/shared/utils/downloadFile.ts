import type { DownloadedFile } from "../api/apiClient";

/** Hand a fetched blob to the browser as a file download. */
export function saveDownloadedFile(
  file: DownloadedFile,
  fallbackFilename: string,
): void {
  const url = URL.createObjectURL(file.blob);

  const link = document.createElement("a");

  link.href = url;
  link.download =
    file.filename ?? fallbackFilename;
  link.rel = "noopener";

  document.body.append(link);
  link.click();
  link.remove();

  URL.revokeObjectURL(url);
}
