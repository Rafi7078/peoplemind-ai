import { apiClient } from "../../api/client";
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
