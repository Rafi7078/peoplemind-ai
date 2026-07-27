import { apiClient } from "../../api/client";
import {
  AUTH_EXPIRED_EVENT,
  tokenSession,
} from "../../auth/session";
import type {
  DocumentAnswerResponse,
  DocumentAskRequest,
  DocumentChunkPreview,
  DocumentIndexResult,
  DocumentPagePreview,
  DocumentProcessResult,
  DocumentRead,
  DocumentSearchRequest,
  DocumentSearchResult,
  DocumentStreamEvent,
} from "./types";
export async function listDocuments(): Promise<
  DocumentRead[]
> {
  const response =
    await apiClient.get<DocumentRead[]>(
      "/api/documents",
    );
  return response.data;
}
export async function uploadDocument(
  file: File,
): Promise<DocumentRead> {
  const formData = new FormData();
  formData.append("file", file);
  const response =
    await apiClient.post<DocumentRead>(
      "/api/documents/upload",
      formData,
      {
        timeout: 120_000,
      },
    );
  return response.data;
}
export async function processDocument(
  documentId: number,
): Promise<DocumentProcessResult> {
  const response =
    await apiClient.post<DocumentProcessResult>(
      `/api/documents/${documentId}/process`,
      undefined,
      {
        timeout: 120_000,
      },
    );
  return response.data;
}
export async function listDocumentPages(
  documentId: number,
): Promise<DocumentPagePreview[]> {
  const response =
    await apiClient.get<DocumentPagePreview[]>(
      `/api/documents/${documentId}/pages`,
    );
  return response.data;
}
export async function indexDocument(
  documentId: number,
): Promise<DocumentIndexResult> {
  const response =
    await apiClient.post<DocumentIndexResult>(
      `/api/documents/${documentId}/index`,
      undefined,
      {
        timeout: 300_000,
      },
    );
  return response.data;
}
export async function listDocumentChunks(
  documentId: number,
): Promise<DocumentChunkPreview[]> {
  const response =
    await apiClient.get<DocumentChunkPreview[]>(
      `/api/documents/${documentId}/chunks`,
    );
  return response.data;
}
export async function searchDocuments(
  request: DocumentSearchRequest,
): Promise<DocumentSearchResult[]> {
  const response =
    await apiClient.post<DocumentSearchResult[]>(
      "/api/documents/search",
      request,
    );
  return response.data;
}
export async function askDocumentQuestion(
  request: DocumentAskRequest,
): Promise<DocumentAnswerResponse> {
  const response =
    await apiClient.post<DocumentAnswerResponse>(
      "/api/documents/ask",
      request,
      {
        timeout: 300_000,
      },
    );
  return response.data;
}

export async function fetchDocumentFile(
  documentId: number,
): Promise<Blob> {
  const response = await apiClient.get<Blob>(
    `/api/documents/${documentId}/file`,
    {
      responseType: "blob",
      timeout: 120_000,
    },
  );
  return response.data;
}

function parseStreamEvent(
  line: string,
): DocumentStreamEvent {
  const parsed: unknown = JSON.parse(line);
  if (
    typeof parsed !== "object" ||
    parsed === null ||
    !("event" in parsed)
  ) {
    throw new Error(
      "The streaming response contained an invalid event.",
    );
  }
  return parsed as DocumentStreamEvent;
}
export async function streamDocumentQuestion(
  request: DocumentAskRequest,
  onEvent: (
    event: DocumentStreamEvent,
  ) => void,
  signal?: AbortSignal,
): Promise<void> {
  const baseUrl = String(
    apiClient.defaults.baseURL ?? "",
  ).replace(/\/$/, "");
  const token = tokenSession.get();
  const headers = new Headers({
    "Content-Type": "application/json",
    Accept: "application/x-ndjson",
  });
  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`,
    );
  }
  const response = await fetch(
    `${baseUrl}/api/documents/ask/stream`,
    {
      method: "POST",
      headers,
      body: JSON.stringify(request),
      signal,
    },
  );
  if (response.status === 401) {
    tokenSession.clear();
    window.dispatchEvent(
      new Event(AUTH_EXPIRED_EVENT),
    );
  }
  if (!response.ok) {
    let message =
      "The streaming request failed.";
    try {
      const errorBody = (
        await response.json()
      ) as {
        detail?: unknown;
      };
      if (
        typeof errorBody.detail ===
        "string"
      ) {
        message = errorBody.detail;
      }
    } catch {
      // Preserve the safe fallback message.
    }
    throw new Error(message);
  }
  if (!response.body) {
    throw new Error(
      "The browser did not receive a streaming response body.",
    );
  }
  const reader =
    response.body.getReader();
  const decoder = new TextDecoder(
    "utf-8",
  );
  let buffer = "";
  while (true) {
    const {
      value,
      done,
    } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(
      value,
      {
        stream: true,
      },
    );
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      const normalizedLine =
        line.trim();
      if (!normalizedLine) {
        continue;
      }
      onEvent(
        parseStreamEvent(
          normalizedLine,
        ),
      );
    }
  }
  buffer += decoder.decode();
  const finalLine = buffer.trim();
  if (finalLine) {
    onEvent(
      parseStreamEvent(finalLine),
    );
  }
}
