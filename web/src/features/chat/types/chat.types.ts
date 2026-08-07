export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  streaming?: boolean;
}
export interface ChatResponse { conversationId: string; runId: string; status: string }
