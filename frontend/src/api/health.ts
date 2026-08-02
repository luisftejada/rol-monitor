import { apiGet } from "./client";

export interface Health {
  status: "ok";
  version: string;
}

export function getHealth(): Promise<Health> {
  return apiGet<Health>("/health");
}
