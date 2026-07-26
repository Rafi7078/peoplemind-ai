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
  indexDocument,
  listDocuments,
  processDocument,
  uploadDocument,
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
  const [question, setQuestion] =
    useState("");
  const [answer, setAnswer] =
    useState<DocumentAnswerResponse | null>(
      null,
    );
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
  async function handleAsk(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    const normalizedQuestion =
      question.trim();
    if (!selectedDocument) {
      setErrorMessage(
        "Select a document first.",
      );
      return;
    }
    if (
      selectedDocument.status !== "indexed"
    ) {
      setErrorMessage(
        "Process and index the selected document before asking questions.",
      );
      return;
    }
    if (normalizedQuestion.length < 3) {
      setErrorMessage(
        "Enter a complete question.",
      );
      return;
    }
    setBusyAction("ask");
    setErrorMessage("");
    setActivityMessage("");
    setAnswer(null);
    try {
      const result =
        await askDocumentQuestion({
          question: normalizedQuestion,
          document_id:
            selectedDocument.id,
          top_k: 5,
        });
      setAnswer(result);
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Question answering failed.",
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
                <p className="mt-4 text-xs leading-5 text-slate-500">
                  Workflow: upload → process →
                  index → ask. Already completed
                  steps remain disabled.
                </p>
              </section>
              <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                <div>
                  <h2 className="text-xl font-bold text-slate-950">
                    Ask this document
                  </h2>
                  <p className="mt-1 text-sm leading-6 text-slate-500">
                    The answer must be supported by
                    retrieved evidence from the
                    selected document.
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
                    <p className="text-xs text-slate-500">
                      Selected document ID:{" "}
                      {selectedDocument.id}
                    </p>
                    <button
                      className="rounded-xl bg-sky-600 px-5 py-3 font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-50"
                      disabled={
                        busyAction !== null ||
                        selectedDocument.status !==
                          "indexed"
                      }
                      type="submit"
                    >
                      {busyAction === "ask"
                        ? "Generating answer..."
                        : "Ask with citations"}
                    </button>
                  </div>
                </form>
              </section>
              {answer ? (
                <section
                  className={[
                    "rounded-3xl border p-6 shadow-sm",
                    answer.answer_found
                      ? "border-emerald-200 bg-white"
                      : "border-amber-200 bg-amber-50",
                  ].join(" ")}
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <h2 className="text-xl font-bold text-slate-950">
                      Answer
                    </h2>
                    <span
                      className={[
                        "rounded-full px-3 py-1 text-xs font-semibold",
                        answer.answer_found
                          ? "bg-emerald-100 text-emerald-700"
                          : "bg-amber-100 text-amber-700",
                      ].join(" ")}
                    >
                      {answer.answer_found
                        ? "Evidence found"
                        : "Reliable evidence unavailable"}
                    </span>
                  </div>
                  <p className="mt-5 whitespace-pre-wrap text-base leading-8 text-slate-800">
                    {answer.answer}
                  </p>
                  <div className="mt-5 flex flex-wrap gap-3 text-xs text-slate-500">
                    <span>
                      Model: {answer.model}
                    </span>
                    <span>
                      Retrieved chunks:{" "}
                      {answer.retrieved_chunks}
                    </span>
                  </div>
                  {answer.citations.length > 0 ? (
                    <div className="mt-6">
                      <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700">
                        Sources
                      </h3>
                      <div className="mt-3 space-y-3">
                        {answer.citations.map(
                          (citation) => (
                            <article
                              className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
                              key={`${citation.source_id}-${citation.chunk_index}`}
                            >
                              <div className="flex flex-wrap items-center gap-2">
                                <span className="rounded-full bg-slate-950 px-2.5 py-1 text-xs font-bold text-white">
                                  {
                                    citation.source_id
                                  }
                                </span>
                                <span className="text-sm font-semibold text-slate-700">
                                  Page{" "}
                                  {
                                    citation.page_number
                                  }
                                </span>
                                <span className="text-xs text-slate-500">
                                  Chunk{" "}
                                  {
                                    citation.chunk_index
                                  }
                                </span>
                              </div>
                              <p className="mt-3 break-words text-sm leading-6 text-slate-600">
                                {
                                  citation.text_preview
                                }
                              </p>
                            </article>
                          ),
                        )}
                      </div>
                    </div>
                  ) : null}
                </section>
              ) : null}
            </>
          )}
        </div>
      </section>
    </main>
  );
}
