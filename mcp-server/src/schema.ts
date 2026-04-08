import { z } from "zod";

type JsonSchemaProperty = {
  description?: string;
  type: string;
};

export function buildToolShape(
  properties: Record<string, unknown>,
  required: Iterable<string> = [],
): Record<string, z.ZodTypeAny> {
  const shape: Record<string, z.ZodTypeAny> = {};
  const requiredFields = new Set(required);

  for (const [key, prop] of Object.entries(properties)) {
    const property = prop as JsonSchemaProperty;
    let field: z.ZodTypeAny;
    switch (property.type) {
      case "number":
        field = z.number();
        break;
      case "boolean":
        field = z.boolean();
        break;
      default:
        field = z.string();
        break;
    }
    field = field.describe(property.description ?? "");
    shape[key] = requiredFields.has(key) ? field : field.optional();
  }

  return shape;
}
