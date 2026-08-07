export interface Approval { id:string; caseId:string; summary:string; status:'pending'|'approved'|'rejected'; requestedAt:string }
