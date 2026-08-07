export function EmptyState({title,description}:{title:string;description?:string}){return <div className="state"><h3>{title}</h3>{description&&<p>{description}</p>}</div>}
