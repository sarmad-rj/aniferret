import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  CheckCircle2,
  ChevronDown,
  ClipboardList,
  ExternalLink,
  Loader2,
  UploadCloud,
  X,
} from "lucide-react";
import useBodyScrollLock from "../hooks/useBodyScrollLock";
import { importMalWatchProgress } from "../lib/api";

const ALLOWED_EXTENSIONS = [".xml", ".gz"];

function isAllowedFile(file) {
  const name = file.name.toLowerCase();
  return ALLOWED_EXTENSIONS.some((extension) => name.endsWith(extension));
}

function CollapsibleList({ label, items }) {
  const [isOpen, setIsOpen] = useState(false);

  if (items.length === 0) {
    return null;
  }

  return (
    <div className="rounded-md border border-[var(--border)] bg-[var(--surface-warm)] p-2">
      <button
        type="button"
        onClick={() => setIsOpen((previous) => !previous)}
        className="flex w-full items-center justify-between text-left text-xs font-medium text-[var(--text)]"
      >
        {label}
        <ChevronDown
          className={`h-3.5 w-3.5 shrink-0 transition-transform ${isOpen ? "rotate-180" : ""}`}
        />
      </button>
      {isOpen && (
        <ul className="mt-2 max-h-32 overflow-y-auto text-xs text-[var(--text-muted)]">
          {items.map((item) => (
            <li key={item} className="truncate py-0.5">
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ImportMalModal({ token, onImportSuccess, onClose }) {
  const [step, setStep] = useState("select");
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [result, setResult] = useState(null);

  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  useBodyScrollLock();

  const handleFileChosen = (file) => {
    if (!file) {
      return;
    }
    if (!isAllowedFile(file)) {
      setErrorMessage(
        "Please choose a .xml or .xml.gz MyAnimeList export file.",
      );
      return;
    }
    setErrorMessage(null);
    setSelectedFile(file);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragActive(false);
    handleFileChosen(event.dataTransfer.files?.[0]);
  };

  const handleReviewSkipped = () => {
    onClose();
    navigate("/app/review-progress", {
      state: { skippedEntries: result.skipped },
    });
  };

  const handleSync = async () => {
    if (!selectedFile) {
      return;
    }

    setErrorMessage(null);
    setStep("uploading");

    try {
      const response = await importMalWatchProgress(token, selectedFile);
      setResult(response);
      setStep("success");
      onImportSuccess?.(response);
    } catch {
      setErrorMessage(
        "Could not import that file. Make sure it's an unmodified MyAnimeList export.",
      );
      setStep("select");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--primary)]/40 p-4">
      <div className="w-full max-w-md rounded-lg bg-[var(--surface)] p-5">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <UploadCloud className="h-4 w-4 text-[var(--ferret)]" />
            <h2 className="text-sm font-semibold text-[var(--primary)]">
              Import from MyAnimeList
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close import MAL progress"
          >
            <X className="h-4 w-4 text-[var(--text-muted)]" />
          </button>
        </div>

        {step === "select" && (
          <div className="flex flex-col gap-3">
            <ol className="list-inside list-decimal space-y-1 text-xs text-[var(--text-muted)]">
              <li>
                Sign in at{" "}
                <a
                  href="https://myanimelist.net/"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-0.5 font-medium text-[var(--primary)] underline"
                >
                  myanimelist.net
                  <ExternalLink className="h-3 w-3" />
                </a>{" "}
                and open your profile
              </li>
              <li>Click the Anime List button, then Export on the left</li>
              <li>Drag the downloaded file below, or browse to select it</li>
              <li>Click Sync Progress</li>
            </ol>

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(event) => {
                event.preventDefault();
                setIsDragActive(true);
              }}
              onDragLeave={() => setIsDragActive(false)}
              onDrop={handleDrop}
              className={`rounded-md border-2 border-dashed p-4 text-center text-xs transition-colors ${
                isDragActive
                  ? "border-[var(--primary)] bg-[var(--surface-warm)]"
                  : "border-[var(--border)] text-[var(--text-muted)]"
              }`}
            >
              {selectedFile ? (
                <span className="font-medium text-[var(--primary)]">
                  {selectedFile.name}
                </span>
              ) : (
                "Drag & drop your export here, or click to browse"
              )}
            </button>

            <input
              ref={fileInputRef}
              type="file"
              accept=".xml,.gz"
              onChange={(event) => handleFileChosen(event.target.files?.[0])}
              className="hidden"
            />

            {errorMessage && (
              <p className="text-xs text-[var(--pink)]">{errorMessage}</p>
            )}

            <button
              type="button"
              onClick={handleSync}
              disabled={!selectedFile}
              className="mt-1 rounded-md bg-[var(--primary)] px-3 py-2 text-sm font-medium text-[var(--surface)] disabled:opacity-50"
            >
              Sync Progress
            </button>
          </div>
        )}

        {step === "uploading" && (
          <div className="flex flex-col items-center gap-2 py-6 text-xs text-[var(--text-muted)]">
            <Loader2 className="h-5 w-5 animate-spin text-[var(--ferret)]" />
            Matching your list against AniFerret's catalog&hellip;
          </div>
        )}

        {step === "success" && result && (
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 rounded-md border border-[var(--border)] bg-[var(--surface-warm)] p-3">
              <CheckCircle2 className="h-5 w-5 shrink-0 text-[var(--sky)]" />
              <p className="text-sm text-[var(--text)]">
                Synced <strong>{result.imported.length}</strong> of{" "}
                {result.total_in_file} entries.
              </p>
            </div>

            <CollapsibleList
              label={`${result.skipped.length} multi-season ${result.skipped.length === 1 ? "entry needs" : "entries need"} manual review`}
              items={result.skipped.map((entry) => entry.title)}
            />
            <CollapsibleList
              label={`${result.unmatched.length} ${result.unmatched.length === 1 ? "title" : "titles"} couldn't be matched`}
              items={result.unmatched}
            />

            {result.skipped.length > 0 && (
              <button
                type="button"
                onClick={handleReviewSkipped}
                className="flex items-center justify-center gap-1.5 rounded-md border border-[var(--primary)] px-3 py-2 text-sm font-medium text-[var(--primary)]"
              >
                <ClipboardList className="h-4 w-4" />
                Set Up{" "}
                {result.skipped.length === 1 ? "That Show" : "Those Shows"} Now
              </button>
            )}

            <button
              type="button"
              onClick={onClose}
              className="rounded-md bg-[var(--primary)] px-3 py-2 text-sm font-medium text-[var(--surface)]"
            >
              Done
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default ImportMalModal;
