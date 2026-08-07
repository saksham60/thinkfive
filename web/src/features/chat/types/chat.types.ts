export interface ChatMessage{id:string;role:'user'|'assistant';content:string;streaming?:boolean} export interface ChatResponse{conversationId:string;runId:string}
