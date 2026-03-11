/** Yuho TypeScript SDK */

export interface YuhoConfig {
  baseUrl: string;
  authToken?: string;
  timeout?: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: { code: string; message: string; details?: any[] };
}

export interface ParseResult {
  statutes: number;
  types: number;
  functions: number;
  imports: number;
  statute_sections: number[];
}

export interface ValidateResult {
  valid: boolean;
  errors: Array<{
    type: string;
    message: string;
    line: number | null;
    column: number | null;
  }>;
}

export interface TranspileResult {
  target: string;
  output: string;
}

export interface LintIssue {
  rule: string;
  severity: string;
  message: string;
  line: number;
  suggestion: string | null;
}

export interface LintResult {
  issues: LintIssue[];
  summary: { errors: number; warnings: number; infos: number; hints: number };
}

export class YuhoClient {
  private baseUrl: string;
  private authToken?: string;
  private timeout: number;

  constructor(config: YuhoConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, '');
    this.authToken = config.authToken;
    this.timeout = config.timeout ?? 30000;
  }

  private async request<T>(method: string, path: string, body?: any): Promise<ApiResponse<T>> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (this.authToken) headers['Authorization'] = `Bearer ${this.authToken}`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);
    try {
      const res = await fetch(`${this.baseUrl}/v1${path}`, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });
      return await res.json();
    } finally {
      clearTimeout(timer);
    }
  }

  async health(): Promise<ApiResponse<any>> {
    return this.request('GET', '/health');
  }

  async parse(source: string, filename?: string): Promise<ApiResponse<ParseResult>> {
    return this.request('POST', '/parse', { source, filename });
  }

  async validate(source: string, options?: { includeMetrics?: boolean; explainErrors?: boolean }): Promise<ApiResponse<ValidateResult>> {
    return this.request('POST', '/validate', {
      source,
      include_metrics: options?.includeMetrics,
      explain_errors: options?.explainErrors,
    });
  }

  async transpile(source: string, target: string = 'json'): Promise<ApiResponse<TranspileResult>> {
    return this.request('POST', '/transpile', { source, target });
  }

  async lint(source: string, rules?: string[]): Promise<ApiResponse<LintResult>> {
    return this.request('POST', '/lint', { source, rules });
  }

  async targets(): Promise<ApiResponse<{ targets: Array<{ name: string; extension: string }> }>> {
    return this.request('GET', '/targets');
  }
}
