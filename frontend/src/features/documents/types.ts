export type DocumentRead = {
  id: number;
  original_name: string;
  size_bytes: number;
  mime_type: string;
  status: string;
  page_count: number | null;
  uploaded_by_id: number;
  created_at: string;
};

export type DocumentDeleteResult = {
  document_id: number;
  deleted: boolean;
  file_deleted: boolean;
};

export type DocumentProcessResult = {
  document_id: number;
  status: string;
  page_count: number;
  text_pages: number;
  total_characters: number;
};
export type DocumentPagePreview = {
  page_number: number;
  char_count: number;
  text_preview: string;
};
export type DocumentIndexResult = {
  document_id: number;
  status: string;
  chunk_count: number;
  vector_dimension: number;
  total_characters: number;
};
export type DocumentChunkPreview = {
  page_number: number;
  chunk_index: number;
  char_count: number;
  text_preview: string;
};
export type DocumentSearchRequest = {
  query: string;
  document_id: number | null;
  top_k: number;
};
export type DocumentSearchResult = {
  vector_id: string;
  document_id: number;
  document_name: string;
  page_number: number;
  chunk_index: number;
  distance: number;
  text: string;
};
export type DocumentAskRequest = {
  question: string;
  document_id: number | null;
  top_k: number;
};
export type AnswerCitation = {
  source_id: string;
  document_id: number;
  document_name: string;
  page_number: number;
  chunk_index: number;
  text_preview: string;
};
export type DocumentResponseType =
  | "conversation"
  | "policy_guidance"
  | "no_supporting_policy";
export type DocumentAnswerResponse = {
  question: string;
  answer: string;
  answer_found: boolean;
  response_type: DocumentResponseType;
  citations: AnswerCitation[];
  retrieved_chunks: number;
  model: string;
};

export type DocumentStreamStatusEvent = {
  event: "status";
  stage: "searching" | "generating";
  message: string;
};
export type DocumentStreamDeltaEvent = {
  event: "delta";
  text: string;
};
export type DocumentStreamFinalEvent = {
  event: "final";
  data: DocumentAnswerResponse;
};
export type DocumentStreamErrorEvent = {
  event: "error";
  message: string;
};
export type DocumentStreamEvent =
  | DocumentStreamStatusEvent
  | DocumentStreamDeltaEvent
  | DocumentStreamFinalEvent
  | DocumentStreamErrorEvent;
