export interface CaseRecord { id:string; alertId?:string; title:string; status:'open'|'pending_approval'|'closed'; updatedAt:string; notes?:Array<{id:string;body:string;createdAt:string}> }
