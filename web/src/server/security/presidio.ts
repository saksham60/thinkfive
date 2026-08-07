import { z } from 'zod';

export interface SecurityCheckResult {
  isSafe: boolean;
  sanitizedText: string;
  piiDetected: string[];
  injectionDetected: boolean;
  reason?: string;
}

export class PresidioGuardrails {
  // Common PII Regex Patterns
  private static CREDIT_CARD_REGEX = /\b(?:\d[ -]*?){13,16}\b/g;
  private static SSN_REGEX = /\b\d{3}[-.\s]??\d{2}[-.\s]??\d{4}\b/g;
  private static CVV_REGEX = /\b(?:cvv|cvc|security code)[\s:]*?(\d{3,4})\b/gi;
  private static PIN_REGEX = /\b(?:pin|passcode)[\s:]*?(\d{4,6})\b/gi;
  private static ACCOUNT_NUM_REGEX = /\b\d{8,12}\b/g;
  private static EMAIL_REGEX = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;

  // Prompt Injection Attack Patterns
  private static INJECTION_PATTERNS = [
    /ignore (?:all )?previous instructions/i,
    /override (?:system )?security/i,
    /bypass (?:fraud|mcp|approval) (?:rules|checks|engine)/i,
    /reveal (?:system prompt|api key|credentials|raw card number)/i,
    /act as (?:admin|root|supervisor) without (?:auth|login|mfa)/i,
    /delete (?:database|audit log|all records)/i,
    /grant me full access/i
  ];

  public static inspectInput(input: string, userRole: string = 'customer'): SecurityCheckResult {
    let sanitized = input;
    const piiDetected: string[] = [];

    // 1. Detect Prompt Injection
    let injectionDetected = false;
    for (const pattern of this.INJECTION_PATTERNS) {
      if (pattern.test(input)) {
        injectionDetected = true;
        return {
          isSafe: false,
          sanitizedText: '[BLOCKED BY GUARDRAILS AI: PROMPT INJECTION DETECTED]',
          piiDetected: [],
          injectionDetected: true,
          reason: 'Potential security policy violation or prompt injection attempt detected.'
        };
      }
    }

    // 2. Detect & Mask PII
    if (this.CREDIT_CARD_REGEX.test(sanitized)) {
      piiDetected.push('CREDIT_CARD_NUMBER');
      sanitized = sanitized.replace(this.CREDIT_CARD_REGEX, (match) => {
        const clean = match.replace(/[\s-]/g, '');
        return `[MASKED_CARD: ****-****-****-${clean.slice(-4)}]`;
      });
    }

    if (this.SSN_REGEX.test(sanitized)) {
      piiDetected.push('SOCIAL_SECURITY_NUMBER');
      sanitized = sanitized.replace(this.SSN_REGEX, '[MASKED_SSN: XXX-XX-****]');
    }

    if (this.CVV_REGEX.test(sanitized)) {
      piiDetected.push('CVV');
      sanitized = sanitized.replace(this.CVV_REGEX, 'CVV: [MASKED_CVV]');
    }

    if (this.PIN_REGEX.test(sanitized)) {
      piiDetected.push('PIN');
      sanitized = sanitized.replace(this.PIN_REGEX, 'PIN: [MASKED_PIN]');
    }

    return {
      isSafe: true,
      sanitizedText: sanitized,
      piiDetected,
      injectionDetected: false
    };
  }

  public static maskOutputText(text: string): string {
    let masked = text;
    // Replace raw card numbers if LLM hallucinates them
    masked = masked.replace(this.CREDIT_CARD_REGEX, '[CARD ending in ****]');
    // Replace raw SSNs
    masked = masked.replace(this.SSN_REGEX, 'XXX-XX-****');
    return masked;
  }
}
