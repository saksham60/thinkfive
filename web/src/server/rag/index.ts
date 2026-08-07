import { db } from '../db';
import { PolicyDocument } from '../../types';

export interface RAGSearchResult {
  document: PolicyDocument;
  relevanceScore: number;
  matchedSnippets: string[];
  citation: {
    docId: string;
    title: string;
    version: string;
    region: string;
    effectiveFrom: string;
    approvedBy: string;
  };
}

export class PolicyRAGEngine {
  public static searchPolicies(query: string, category?: string): RAGSearchResult[] {
    const policies = db.getPolicies();
    const queryTerms = query.toLowerCase().split(/\s+/).filter(t => t.length > 2);
    const results: RAGSearchResult[] = [];

    for (const policy of policies) {
      if (category && policy.category !== category) continue;

      const contentLower = policy.content.toLowerCase();
      const titleLower = policy.title.toLowerCase();

      let matchCount = 0;
      const matchedSnippets: string[] = [];

      // Keyword matching
      for (const term of queryTerms) {
        if (titleLower.includes(term)) matchCount += 3;
        if (contentLower.includes(term)) matchCount += 1;
      }

      // Extract matching lines or sections
      const lines = policy.content.split('\n');
      for (const line of lines) {
        if (queryTerms.some(term => line.toLowerCase().includes(term))) {
          matchedSnippets.push(line.trim());
        }
      }

      if (matchCount > 0) {
        const relevanceScore = Math.min(1.0, 0.2 + (matchCount * 0.15));
        results.push({
          document: policy,
          relevanceScore,
          matchedSnippets: matchedSnippets.length > 0 ? matchedSnippets : [lines[0]],
          citation: {
            docId: policy.documentId,
            title: policy.title,
            version: policy.version,
            region: policy.region,
            effectiveFrom: policy.effectiveFrom,
            approvedBy: policy.approvedBy
          }
        });
      }
    }

    return results.sort((a, b) => b.relevanceScore - a.relevanceScore);
  }
}
