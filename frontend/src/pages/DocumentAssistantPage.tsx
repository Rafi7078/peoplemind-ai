import axios from "axios";
import {
  useEffect,
  useMemo,
  useState,
} from "react";
import type {
  FormEvent,
} from "react";
import {
  askDocumentQuestion,
  fetchDocumentFile,
  indexDocument,
  listDocuments,
  processDocument,
  streamDocumentQuestion,
  uploadDocument,
  deleteDocument,
  renameDocument,
} from "../features/documents/api";
import type {
  DocumentAnswerResponse,
  DocumentRead,
} from "../features/documents/types";
function formatBytes(size: number): string {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(
    size /
    (1024 * 1024)
  ).toFixed(1)} MB`;
}
function formatDate(value: string): string {
  return new Intl.DateTimeFormat(
    "en-US",
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(new Date(value));
}
type PolicyDisplayMetadata = {
  title: string;
  documentDate: string | null;
};
function getPolicyDisplayMetadata(
  filename: string,
): PolicyDisplayMetadata {
  const filenameWithoutExtension =
    filename.replace(/\.pdf$/i, "");
  const datedFilenamePattern =
    /^(.*?)\s+-\s+((?:\d{1,2}\s+)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})$/i;
  const match =
    filenameWithoutExtension.match(
      datedFilenamePattern,
    );
  if (!match) {
    return {
      title: filenameWithoutExtension,
      documentDate: null,
    };
  }
  return {
    title: match[1].trim(),
    documentDate: match[2].trim(),
  };
}
function formatSourceNumber(
  sourceId: string,
): string {
  const sourceNumber = sourceId.replace(
    /^S/i,
    "",
  );
  return `[${sourceNumber}]`;
}
function formatPolicyAnswer(
  answer: string,
): string {
  return answer.replace(
    /\[S(\d+)\]/gi,
    "[$1]",
  );
}
function statusClass(status: string): string {
  switch (status.toLowerCase()) {
    case "indexed":
      return "bg-emerald-100 text-emerald-700";
    case "ready":
      return "bg-sky-100 text-sky-700";
    case "uploaded":
      return "bg-amber-100 text-amber-700";
    case "processing":
      return "bg-violet-100 text-violet-700";
    case "failed":
    case "needs_ocr":
      return "bg-red-100 text-red-700";
    default:
      return "bg-slate-100 text-slate-600";
  }
}
function getApiErrorMessage(
  error: unknown,
  fallback: string,
): string {
  if (!axios.isAxiosError(error)) {
    return fallback;
  }
  if (
    error.code === "ECONNABORTED" ||
    error.code === "ETIMEDOUT"
  ) {
    return (
      "The local AI request took too long. " +
      "Keep Ollama running and try again."
    );
  }
  if (!error.response) {
    return (
      "Backend server is not reachable. " +
      "Confirm that FastAPI is running."
    );
  }
  const responseData =
    error.response.data as {
      detail?: unknown;
    };
  if (
    typeof responseData.detail === "string"
  ) {
    return responseData.detail;
  }
  return fallback;
}
export function DocumentAssistantPage() {
  const [documents, setDocuments] =
    useState<DocumentRead[]>([]);
  const [
    selectedDocumentId,
    setSelectedDocumentId,
  ] = useState<number | null>(null);
  const [searchScope, setSearchScope] =
    useState<"all" | "selected">("all");
  const [question, setQuestion] =
    useState("");
  const [answer, setAnswer] =
    useState<DocumentAnswerResponse | null>(
      null,
    );
  const [streamingText, setStreamingText] =
    useState("");
  const [streamStatus, setStreamStatus] =
    useState("");
  const [isLoading, setIsLoading] =
    useState(true);
  const [busyAction, setBusyAction] =
    useState<string | null>(null);
  const [errorMessage, setErrorMessage] =
    useState("");
  const [
    activityMessage,
    setActivityMessage,
  ] = useState("");
  const [
    renameTarget,
    setRenameTarget,
  ] = useState<DocumentRead | null>(null);
  const [
    renameName,
    setRenameName,
  ] = useState("");
  const [
    deleteTarget,
    setDeleteTarget,
  ] = useState<DocumentRead | null>(null);
  const selectedDocument = useMemo(
    () =>
      documents.find(
        (document) =>
          document.id === selectedDocumentId,
      ) ?? null,
    [
      documents,
      selectedDocumentId,
    ],
  );
  useEffect(() => {
    document.title =
      "Document Assistant | PeopleMind AI";
    let isActive = true;
    listDocuments()
      .then((result) => {
        if (!isActive) {
          return;
        }
        setDocuments(result);
        if (result.length > 0) {
          setSelectedDocumentId(
            result[0].id,
          );
        }
      })
      .catch((error: unknown) => {
        if (!isActive) {
          return;
        }
        setErrorMessage(
          getApiErrorMessage(
            error,
            "Could not load documents.",
          ),
        );
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
        }
      });
    return () => {
      isActive = false;
    };
  }, []);
  function updateDocument(
    documentId: number,
    changes: Partial<DocumentRead>,
  ): void {
    setDocuments((currentDocuments) =>
      currentDocuments.map((document) =>
        document.id === documentId
          ? {
              ...document,
              ...changes,
            }
          : document,
      ),
    );
  }
  async function handleRefresh(): Promise<void> {
    setBusyAction("refresh");
    setErrorMessage("");
    setActivityMessage("");
    try {
      const result = await listDocuments();
      setDocuments(result);
      setSelectedDocumentId(
        (currentDocumentId) => {
          if (
            currentDocumentId !== null &&
            result.some(
              (document) =>
                document.id ===
                currentDocumentId,
            )
          ) {
            return currentDocumentId;
          }
          return result[0]?.id ?? null;
        },
      );
      setActivityMessage(
        "Document list refreshed.",
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not refresh documents.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  async function handleUpload(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const file = formData.get("document");
    if (!(file instanceof File)) {
      setErrorMessage(
        "Select a PDF document first.",
      );
      return;
    }
    if (
      file.type !== "application/pdf" &&
      !file.name.toLowerCase().endsWith(".pdf")
    ) {
      setErrorMessage(
        "Only PDF documents are supported.",
      );
      return;
    }
    setBusyAction("upload");
    setErrorMessage("");
    setActivityMessage("");
    setAnswer(null);
    try {
      const uploadedDocument =
        await uploadDocument(file);
      setDocuments((currentDocuments) => [
        uploadedDocument,
        ...currentDocuments.filter(
          (document) =>
            document.id !==
            uploadedDocument.id,
        ),
      ]);
      setSelectedDocumentId(
        uploadedDocument.id,
      );
      form.reset();
      setActivityMessage(
        `${uploadedDocument.original_name} uploaded successfully.`,
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Document upload failed.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  async function handleProcess(
    document: DocumentRead,
  ): Promise<void> {
    setBusyAction(
      `process:${document.id}`,
    );
    setErrorMessage("");
    setActivityMessage("");
    setAnswer(null);
    try {
      const result =
        await processDocument(document.id);
      updateDocument(
        document.id,
        {
          status: result.status,
          page_count: result.page_count,
        },
      );
      setActivityMessage(
        `Processing complete: ${result.text_pages} text pages and ${result.total_characters} characters extracted.`,
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Document processing failed.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  async function handleIndex(
    document: DocumentRead,
  ): Promise<void> {
    setBusyAction(
      `index:${document.id}`,
    );
    setErrorMessage("");
    setActivityMessage("");
    setAnswer(null);
    try {
      const result =
        await indexDocument(document.id);
      updateDocument(
        document.id,
        {
          status: result.status,
        },
      );
      setActivityMessage(
        `Index created: ${result.chunk_count} chunks with ${result.vector_dimension}-dimension embeddings.`,
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Document indexing failed.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  async function handleRename(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    if (!renameTarget) {
      return;
    }
    const normalizedName =
      renameName.trim();
    if (!normalizedName) {
      setErrorMessage(
        "Enter a document name.",
      );
      return;
    }
    if (
      normalizedName.includes("/") ||
      normalizedName.includes("\\")
    ) {
      setErrorMessage(
        "The document name cannot contain path characters.",
      );
      return;
    }
    if (
      !normalizedName
        .toLowerCase()
        .endsWith(".pdf")
    ) {
      setErrorMessage(
        "The document name must end with .pdf.",
      );
      return;
    }
    if (
      normalizedName
        .toLowerCase()
        .endsWith(".pdf.pdf")
    ) {
      setErrorMessage(
        "Remove the repeated .pdf extension.",
      );
      return;
    }
    if (
      normalizedName ===
      renameTarget.original_name
    ) {
      setRenameTarget(null);
      setRenameName("");
      return;
    }
    const targetId =
      renameTarget.id;
    setBusyAction(
      `rename:${targetId}`,
    );
    setErrorMessage("");
    setActivityMessage("");
    try {
      const renamedDocument =
        await renameDocument(
          targetId,
          normalizedName,
        );
      updateDocument(
        targetId,
        {
          original_name:
            renamedDocument.original_name,
        },
      );
      setAnswer(null);
      setRenameTarget(null);
      setRenameName("");
      setActivityMessage(
        `${renamedDocument.original_name} renamed successfully.`,
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Document rename failed.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  async function handleDeleteConfirmed():
    Promise<void> {
    if (!deleteTarget) {
      return;
    }
    const targetDocument =
      deleteTarget;
    setBusyAction(
      `delete:${targetDocument.id}`,
    );
    setErrorMessage("");
    setActivityMessage("");
    try {
      const result =
        await deleteDocument(
          targetDocument.id,
        );
      const remainingDocuments =
        documents.filter(
          (document) =>
            document.id !==
            targetDocument.id,
        );
      setDocuments(
        remainingDocuments,
      );
      setSelectedDocumentId(
        (currentDocumentId) => {
          if (
            currentDocumentId ===
            targetDocument.id
          ) {
            return (
              remainingDocuments[0]?.id ??
              null
            );
          }
          return currentDocumentId;
        },
      );
      setSearchScope("all");
      setAnswer(null);
      setStreamingText("");
      setStreamStatus("");
      setDeleteTarget(null);
      setActivityMessage(
        result.file_deleted
          ? `${targetDocument.original_name} and all indexed data were deleted.`
          : (
              `${targetDocument.original_name} was removed, ` +
              "but the stored file could not be deleted."
            ),
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Document deletion failed.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  async function handleAsk(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    const normalizedQuestion =
      question.trim();
    if (normalizedQuestion.length < 1) {
      setErrorMessage(
        "Enter a message or policy question.",
      );
      return;
    }
    const request = {
      question: normalizedQuestion,
      document_id:
        searchScope === "selected" &&
        selectedDocument?.status ===
          "indexed"
          ? selectedDocument.id
          : null,
      top_k: 5,
    };
    let receivedTextDelta = false;
    let receivedFinalEvent = false;
    setBusyAction("ask");
    setErrorMessage("");
    setActivityMessage("");
    setAnswer(null);
    setStreamingText("");
    setStreamStatus(
      "Preparing your request...",
    );
    try {
      await streamDocumentQuestion(
        request,
        (streamEvent) => {
          switch (streamEvent.event) {
            case "status":
              setStreamStatus(
                streamEvent.message,
              );
              break;
            case "delta":
              receivedTextDelta = true;
              setStreamStatus(
                "Generating policy guidance...",
              );
              setStreamingText(
                (currentText) =>
                  currentText +
                  streamEvent.text,
              );
              break;
            case "final":
              receivedFinalEvent = true;
              setAnswer(
                streamEvent.data,
              );
              setStreamingText("");
              setStreamStatus("");
              break;
            case "error":
              throw new Error(
                streamEvent.message,
              );
          }
        },
      );
      if (!receivedFinalEvent) {
        throw new Error(
          "The streaming response ended before completion.",
        );
      }
    } catch (streamError) {
      /*
       * A standard response is safe when no
       * answer text has appeared yet. Once live
       * text has started, repeating the complete
       * model request would waste time and CPU.
       */
      if (!receivedTextDelta) {
        setStreamingText("");
        setStreamStatus(
          "Completing with the standard response...",
        );
        try {
          const fallbackResult =
            await askDocumentQuestion(
              request,
            );
          setAnswer(fallbackResult);
          setStreamStatus("");
        } catch (fallbackError) {
          setStreamStatus("");
          setErrorMessage(
            getApiErrorMessage(
              fallbackError,
              "Question answering failed.",
            ),
          );
        }
      } else {
        setStreamingText("");
        setStreamStatus("");
        setErrorMessage(
          streamError instanceof Error &&
          streamError.message
            ? streamError.message
            : (
                "The live response was interrupted. " +
                "Please try again."
              ),
        );
      }
    } finally {
      setBusyAction(null);
    }
  }
  async function handleOpenPolicy(
    documentId: number,
    pageNumber: number,
  ): Promise<void> {
    const policyWindow = window.open(
      "about:blank",
      "_blank",
    );
    if (!policyWindow) {
      setErrorMessage(
        "Your browser blocked the policy window. Allow pop-ups and try again.",
      );
      return;
    }
    policyWindow.opener = null;
    const actionKey =
      `open:${documentId}:${pageNumber}`;
    setBusyAction(actionKey);
    setErrorMessage("");
    setActivityMessage("");
    try {
      const policyBlob =
        await fetchDocumentFile(documentId);
      const objectUrl =
        URL.createObjectURL(policyBlob);
      policyWindow.location.replace(
        `${objectUrl}#page=${pageNumber}`,
      );
      window.setTimeout(() => {
        URL.revokeObjectURL(objectUrl);
      }, 300_000);
    } catch (error) {
      policyWindow.close();
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not open the referenced policy.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <section className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-sky-600">
            Evidence-grounded local AI
          </p>
          <h1 className="mt-2 text-3xl font-bold text-slate-950">
            Document Assistant
          </h1>
          <p className="mt-2 max-w-3xl leading-7 text-slate-600">
            Upload an HR PDF, extract its text,
            create a semantic index and ask
            questions with page-level citations.
          </p>
        </div>
        <button
          className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-60"
          disabled={busyAction !== null}
          onClick={() => {
            void handleRefresh();
          }}
          type="button"
        >
          {busyAction === "refresh"
            ? "Refreshing..."
            : "Refresh documents"}
        </button>
      </section>
      {errorMessage ? (
        <div
          className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700"
          role="alert"
        >
          {errorMessage}
        </div>
      ) : null}
      {activityMessage ? (
        <div
          className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm font-medium text-emerald-700"
          role="status"
        >
          {activityMessage}
        </div>
      ) : null}
      <section className="mt-8 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <h2 className="text-lg font-bold text-slate-900">
            Upload HR document
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            PDF only. Maximum size is controlled
            securely by the backend.
          </p>
        </div>
        <form
          className="mt-5 flex flex-col gap-3 sm:flex-row"
          onSubmit={handleUpload}
        >
          <input
            accept="application/pdf,.pdf"
            className="min-w-0 flex-1 rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-700 file:mr-4 file:rounded-lg file:border-0 file:bg-slate-950 file:px-4 file:py-2 file:font-semibold file:text-white"
            name="document"
            required
            type="file"
          />
          <button
            className="rounded-xl bg-sky-600 px-5 py-3 font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={busyAction !== null}
            type="submit"
          >
            {busyAction === "upload"
              ? "Uploading..."
              : "Upload PDF"}
          </button>
        </form>
      </section>
      <section className="mt-8 grid gap-6 lg:grid-cols-[360px_minmax(0,1fr)]">
        <aside className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-slate-900">
              Documents
            </h2>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
              {documents.length}
            </span>
          </div>
          <div className="mt-4 space-y-3">
            {isLoading ? (
              <p className="rounded-xl bg-slate-50 px-4 py-5 text-center text-sm text-slate-500">
                Loading documents...
              </p>
            ) : null}
            {!isLoading &&
            documents.length === 0 ? (
              <p className="rounded-xl border border-dashed border-slate-300 px-4 py-8 text-center text-sm leading-6 text-slate-500">
                No documents uploaded yet.
              </p>
            ) : null}
            {documents.map((document) => {
              const isSelected =
                document.id ===
                selectedDocumentId;
              return (
                <button
                  className={[
                    "w-full rounded-2xl border p-4 text-left transition",
                    isSelected
                      ? "border-sky-500 bg-sky-50 ring-2 ring-sky-100"
                      : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50",
                  ].join(" ")}
                  key={document.id}
                  onClick={() => {
                    setSelectedDocumentId(
                      document.id,
                    );
                    if (
                      document.status !== "indexed"
                    ) {
                      setSearchScope("all");
                    }
                    setAnswer(null);
                    setErrorMessage("");
                    setActivityMessage("");
                  }}
                  type="button"
                >
                  <div className="flex items-start justify-between gap-3">
                    <p className="min-w-0 break-words text-sm font-bold text-slate-900">
                      {document.original_name}
                    </p>
                    <span
                      className={`shrink-0 rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase ${statusClass(document.status)}`}
                    >
                      {document.status}
                    </span>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-500">
                    <span>
                      {formatBytes(
                        document.size_bytes,
                      )}
                    </span>
                    <span>
                      {document.page_count ??
                        "—"}{" "}
                      pages
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </aside>
        <div className="space-y-6">
          {!selectedDocument ? (
            <section className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
              <h2 className="text-xl font-bold text-slate-900">
                Select a document
              </h2>
              <p className="mt-2 text-slate-500">
                Choose an uploaded document to
                process, index and query.
              </p>
            </section>
          ) : (
            <>
              <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-start">
                  <div className="min-w-0">
                    <span
                      className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold uppercase ${statusClass(selectedDocument.status)}`}
                    >
                      {selectedDocument.status}
                    </span>
                    <h2 className="mt-3 break-words text-xl font-bold text-slate-950">
                      {
                        selectedDocument.original_name
                      }
                    </h2>
                    <p className="mt-2 text-sm text-slate-500">
                      Uploaded{" "}
                      {formatDate(
                        selectedDocument.created_at,
                      )}
                    </p>
                  </div>
                  <div className="grid shrink-0 grid-cols-2 gap-3 text-center">
                    <div className="rounded-xl bg-slate-100 px-4 py-3">
                      <p className="text-lg font-bold text-slate-900">
                        {selectedDocument.page_count ??
                          "—"}
                      </p>
                      <p className="text-xs text-slate-500">
                        Pages
                      </p>
                    </div>
                    <div className="rounded-xl bg-slate-100 px-4 py-3">
                      <p className="text-lg font-bold text-slate-900">
                        {formatBytes(
                          selectedDocument.size_bytes,
                        )}
                      </p>
                      <p className="text-xs text-slate-500">
                        File size
                      </p>
                    </div>
                  </div>
                </div>
                <div className="mt-6 grid gap-3 sm:grid-cols-2">
                  <button
                    className="rounded-xl border border-slate-300 bg-white px-4 py-3 font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={
                      busyAction !== null ||
                      ![
                        "uploaded",
                        "failed",
                      ].includes(
                        selectedDocument.status,
                      )
                    }
                    onClick={() => {
                      void handleProcess(
                        selectedDocument,
                      );
                    }}
                    type="button"
                  >
                    {busyAction ===
                    `process:${selectedDocument.id}`
                      ? "Processing PDF..."
                      : "1. Process PDF"}
                  </button>
                  <button
                    className="rounded-xl bg-slate-950 px-4 py-3 font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={
                      busyAction !== null ||
                      selectedDocument.status !==
                        "ready"
                    }
                    onClick={() => {
                      void handleIndex(
                        selectedDocument,
                      );
                    }}
                    type="button"
                  >
                    {busyAction ===
                    `index:${selectedDocument.id}`
                      ? "Creating index..."
                      : "2. Create vector index"}
                  </button>
                </div>
                <div className="mt-4 flex flex-wrap gap-3 border-t border-slate-200 pt-4">
                  <button
                    className="rounded-xl border border-sky-200 bg-sky-50 px-4 py-2.5 text-sm font-semibold text-sky-700 transition hover:bg-sky-100 disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={
                      busyAction !== null
                    }
                    onClick={() => {
                      setRenameTarget(
                        selectedDocument,
                      );
                      setRenameName(
                        selectedDocument.original_name,
                      );
                      setErrorMessage("");
                      setActivityMessage("");
                    }}
                    type="button"
                  >
                    Rename document
                  </button>
                  <button
                    className="rounded-xl border border-red-200 bg-red-50 px-4 py-2.5 text-sm font-semibold text-red-700 transition hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={
                      busyAction !== null
                    }
                    onClick={() => {
                      setDeleteTarget(
                        selectedDocument,
                      );
                      setErrorMessage("");
                      setActivityMessage("");
                    }}
                    type="button"
                  >
                    Delete document
                  </button>
                </div>
                <p className="mt-4 text-xs leading-5 text-slate-500">
                  Workflow: upload → process →
                  index → ask. Already completed
                  steps remain disabled.
                </p>
              </section>
              <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                <div>
                  <h2 className="text-xl font-bold text-slate-950">
                    Ask PeopleMind AI
                  </h2>
                  <p className="mt-1 text-sm leading-6 text-slate-500">
                    Ask a company-policy question or
                    send a greeting. Policy answers
                    are always grounded in indexed
                    company documents.
                  </p>
                </div>
                <form
                  className="mt-5"
                  onSubmit={handleAsk}
                >
                  <textarea
                    className="min-h-32 w-full resize-y rounded-2xl border border-slate-300 bg-slate-50 px-4 py-4 text-slate-900 outline-none transition focus:border-sky-500 focus:bg-white focus:ring-4 focus:ring-sky-100"
                    onChange={(event) => {
                      setQuestion(
                        event.target.value,
                      );
                    }}
                    placeholder="Example: How many casual leave days does an employee receive each year?"
                    value={question}
                  />
                  <div className="mt-3 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
                    <div className="flex flex-col gap-2">
                      <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                        Search scope
                      </p>
                      <div className="inline-flex w-fit rounded-xl border border-slate-200 bg-slate-100 p-1">
                        <button
                          className={[
                            "rounded-lg px-3 py-2 text-xs font-semibold transition",
                            searchScope === "all"
                              ? "bg-white text-sky-700 shadow-sm"
                              : "text-slate-600 hover:text-slate-900",
                          ].join(" ")}
                          onClick={() => {
                            setSearchScope("all");
                            setAnswer(null);
                            setErrorMessage("");
                          }}
                          type="button"
                        >
                          All company policies
                        </button>
                        <button
                          className={[
                            "rounded-lg px-3 py-2 text-xs font-semibold transition",
                            searchScope === "selected"
                              ? "bg-white text-sky-700 shadow-sm"
                              : "text-slate-600 hover:text-slate-900",
                          ].join(" ")}
                          disabled={
                            selectedDocument.status !==
                            "indexed"
                          }
                          onClick={() => {
                            setSearchScope(
                              "selected",
                            );
                            setAnswer(null);
                            setErrorMessage("");
                          }}
                          type="button"
                        >
                          This policy only
                        </button>
                      </div>
                      <p className="max-w-md break-words text-xs text-slate-500">
                        {searchScope === "all"
                          ? "Searching across all indexed company policies."
                          : `Searching only: ${selectedDocument.original_name.replace(
                              /\.pdf$/i,
                              "",
                            )}`}
                      </p>
                    </div>
                    <button
                      className="rounded-xl bg-sky-600 px-5 py-3 font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-50"
                      disabled={
                        busyAction !== null
                      }
                      type="submit"
                    >
                      {busyAction === "ask"
                        ? "Generating answer..."
                        : "Ask PeopleMind AI"}
                    </button>
                  </div>
                </form>
              </section>
              {busyAction === "ask" &&
              !answer ? (
                <section className="rounded-3xl border border-sky-200 bg-white p-6 shadow-sm">
                  <div className="flex items-start gap-4">
                    <div
                      aria-hidden="true"
                      className="mt-1 h-9 w-9 shrink-0 animate-spin rounded-full border-4 border-sky-100 border-t-sky-600"
                    />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-bold uppercase tracking-[0.18em] text-sky-700">
                        {streamingText
                          ? "Policy Guidance"
                          : "PeopleMind AI"}
                      </p>
                      <h2 className="mt-2 text-lg font-bold text-slate-950">
                        {streamStatus ||
                          "Preparing response..."}
                      </h2>
                      {streamingText ? (
                        <p className="mt-5 whitespace-pre-wrap text-base leading-8 text-slate-800">
                          {formatPolicyAnswer(
                            streamingText,
                          )}
                          <span
                            aria-hidden="true"
                            className="ml-1 inline-block animate-pulse font-bold text-sky-600"
                          >
                            |
                          </span>
                        </p>
                      ) : (
                        <p className="mt-2 text-sm leading-6 text-slate-500">
                          Relevant company policies are
                          being reviewed. The answer will
                          appear here as it is generated.
                        </p>
                      )}
                    </div>
                  </div>
                </section>
              ) : null}
              {answer ? (
                <>
                  {answer.response_type ===
                  "conversation" ? (
                    <section className="rounded-3xl border border-sky-200 bg-sky-50 p-6 shadow-sm">
                      <p className="text-sm font-bold uppercase tracking-[0.16em] text-sky-700">
                        PeopleMind AI
                      </p>
                      <p className="mt-4 whitespace-pre-wrap text-base leading-8 text-slate-800">
                        {answer.answer}
                      </p>
                    </section>
                  ) : null}
                  {answer.response_type ===
                  "no_supporting_policy" ? (
                    <section className="rounded-3xl border border-amber-200 bg-amber-50 p-6 shadow-sm">
                      <div className="flex items-start gap-4">
                        <div
                          aria-hidden="true"
                          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-amber-100 text-lg font-bold text-amber-700"
                        >
                          !
                        </div>
                        <div>
                          <h2 className="text-xl font-bold text-slate-950">
                            No supporting policy found
                          </h2>
                          <p className="mt-2 max-w-2xl leading-7 text-slate-600">
                            We could not find sufficient
                            information in the available
                            company policies to answer this
                            question reliably. Try rephrasing
                            the question or selecting a more
                            relevant policy.
                          </p>
                        </div>
                      </div>
                    </section>
                  ) : null}
                  {answer.response_type ===
                  "policy_guidance" ? (
                    <section className="rounded-3xl border border-emerald-200 bg-white p-6 shadow-sm">
                      <div>
                        <p className="text-sm font-bold uppercase tracking-[0.18em] text-emerald-700">
                          Policy Guidance
                        </p>
                        <p className="mt-5 whitespace-pre-wrap text-base leading-8 text-slate-800">
                          {formatPolicyAnswer(
                            answer.answer,
                          )}
                        </p>
                      </div>
                      {answer.citations.length >
                      0 ? (
                        <div className="mt-8 border-t border-slate-200 pt-6">
                          <h3 className="text-sm font-bold uppercase tracking-[0.18em] text-slate-700">
                            Supporting References
                          </h3>
                          <div className="mt-4 space-y-4">
                            {answer.citations.map(
                              (citation) => {
                                const metadata =
                                  getPolicyDisplayMetadata(
                                    citation.document_name,
                                  );
                                const actionKey =
                                  `open:${citation.document_id}:${citation.page_number}`;
                                return (
                                  <article
                                    className="rounded-2xl border border-slate-200 bg-slate-50 p-5"
                                    key={`${citation.source_id}-${citation.document_id}-${citation.page_number}-${citation.chunk_index}`}
                                  >
                                    <div className="flex items-start gap-3">
                                      <span className="flex h-8 min-w-8 shrink-0 items-center justify-center rounded-full bg-slate-950 px-2 text-xs font-bold text-white">
                                        {formatSourceNumber(
                                          citation.source_id,
                                        )}
                                      </span>
                                      <div className="min-w-0 flex-1">
                                        <h4 className="break-words text-base font-bold text-slate-900">
                                          {metadata.title}
                                        </h4>
                                        <p className="mt-1 text-sm leading-6 text-slate-500">
                                          {metadata.documentDate
                                            ? `Document date: ${metadata.documentDate} | `
                                            : ""}
                                          Referenced on page{" "}
                                          {
                                            citation.page_number
                                          }
                                        </p>
                                        <button
                                          className="mt-4 inline-flex items-center gap-2 rounded-lg text-sm font-bold text-sky-700 transition hover:text-sky-900 disabled:cursor-not-allowed disabled:opacity-50"
                                          disabled={
                                            busyAction !==
                                            null
                                          }
                                          onClick={() => {
                                            void handleOpenPolicy(
                                              citation.document_id,
                                              citation.page_number,
                                            );
                                          }}
                                          type="button"
                                        >
                                          {busyAction ===
                                          actionKey
                                            ? "Opening policy..."
                                            : "View referenced policy"}
                                        </button>
                                      </div>
                                    </div>
                                  </article>
                                );
                              },
                            )}
                          </div>
                        </div>
                      ) : null}
                    </section>
                  ) : null}
                </>
              ) : null}
            </>
          )}
        </div>
      </section>
      {renameTarget ? (
        <div
          aria-labelledby="rename-document-title"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4"
          role="dialog"
        >
          <form
            className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl"
            onSubmit={handleRename}
          >
            <p className="text-sm font-bold uppercase tracking-[0.16em] text-sky-700">
              Document management
            </p>
            <h2
              className="mt-2 text-2xl font-bold text-slate-950"
              id="rename-document-title"
            >
              Rename document
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              The displayed policy name and citation
              metadata will be updated. The secured
              stored PDF will remain unchanged.
            </p>
            <label
              className="mt-5 block text-sm font-semibold text-slate-700"
              htmlFor="document-rename"
            >
              PDF name
            </label>
            <input
              autoFocus
              className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-sky-500 focus:ring-4 focus:ring-sky-100"
              id="document-rename"
              maxLength={255}
              onChange={(event) => {
                setRenameName(
                  event.target.value,
                );
              }}
              required
              type="text"
              value={renameName}
            />
            <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
              <button
                className="rounded-xl border border-slate-300 px-4 py-3 font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
                disabled={
                  busyAction !== null
                }
                onClick={() => {
                  setRenameTarget(null);
                  setRenameName("");
                }}
                type="button"
              >
                Cancel
              </button>
              <button
                className="rounded-xl bg-sky-600 px-5 py-3 font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-50"
                disabled={
                  busyAction !== null
                }
                type="submit"
              >
                {busyAction ===
                `rename:${renameTarget.id}`
                  ? "Renaming..."
                  : "Save new name"}
              </button>
            </div>
          </form>
        </div>
      ) : null}
      {deleteTarget ? (
        <div
          aria-labelledby="delete-document-title"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4"
          role="dialog"
        >
          <div className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-100 text-xl font-bold text-red-700">
              !
            </div>
            <h2
              className="mt-4 text-2xl font-bold text-slate-950"
              id="delete-document-title"
            >
              Delete this document?
            </h2>
            <p className="mt-3 break-words text-sm font-semibold text-slate-800">
              {deleteTarget.original_name}
            </p>
            <p className="mt-3 text-sm leading-6 text-slate-500">
              This permanently removes the uploaded PDF,
              extracted pages, searchable chunks and
              ChromaDB vectors. This action cannot be
              undone.
            </p>
            <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
              <button
                className="rounded-xl border border-slate-300 px-4 py-3 font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
                disabled={
                  busyAction !== null
                }
                onClick={() => {
                  setDeleteTarget(null);
                }}
                type="button"
              >
                Keep document
              </button>
              <button
                className="rounded-xl bg-red-600 px-5 py-3 font-semibold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
                disabled={
                  busyAction !== null
                }
                onClick={() => {
                  void handleDeleteConfirmed();
                }}
                type="button"
              >
                {busyAction ===
                `delete:${deleteTarget.id}`
                  ? "Deleting..."
                  : "Delete permanently"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}
