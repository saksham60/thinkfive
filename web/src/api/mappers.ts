export type JsonObject = Record<string, unknown>;

export const asObject = (value: unknown): JsonObject =>
  typeof value === 'object' && value !== null && !Array.isArray(value)
    ? value as JsonObject
    : {};

export const asArray = (value: unknown): unknown[] => Array.isArray(value) ? value : [];

export const stringValue = (value: unknown, fallback = ''): string =>
  typeof value === 'string' ? value : value == null ? fallback : String(value);

export const optionalString = (value: unknown): string | undefined => {
  const result = stringValue(value).trim();
  return result || undefined;
};

export const numberValue = (value: unknown, fallback = 0): number => {
  const result = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(result) ? result : fallback;
};

export const booleanValue = (value: unknown): boolean =>
  value === true || value === 'true' || value === 1;

export const arrayFromEnvelope = (value: unknown, key: string): unknown[] => {
  if (Array.isArray(value)) return value;
  return asArray(asObject(value)[key]);
};

export const firstValue = (object: JsonObject, keys: string[]): unknown => {
  for (const key of keys) {
    if (object[key] !== undefined && object[key] !== null) return object[key];
  }
  return undefined;
};

export const humanize = (value: string): string =>
  value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
