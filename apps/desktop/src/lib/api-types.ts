export type ErrorEnvelope = {
  error: {
    code: string;
    message: string;
    fields?: Record<string, string>;
    request_id: string;
  };
};

export type SessionResponse = {
  authenticated: true;
  currency: "THB";
  timezone: "Asia/Bangkok";
  units: { weight: "kg"; water: "ml" };
};

export type HealthResponse = { status: "ok" };

export type ListResponse<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};
