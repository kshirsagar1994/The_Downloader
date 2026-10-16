import { ExtractionResult, CreateJobRequest, JobProgressEvent } from "../types/media";

export class ApiError extends Error {
  code: string;
  status?: number;
  retryable?: boolean;
  userAction?: string;
  jobId?: string;

  constructor(
    message: string,
    code: string = "REQUEST_FAILED",
    status?: number,
    retryable?: boolean,
    userAction?: string,
    jobId?: string
  ) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.retryable = retryable;
    this.userAction = userAction;
    this.jobId = jobId;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  const text = await response.text();
  let data: any = null;

  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    const isHtml = text.trim().startsWith("<") || text.includes("<html") || text.includes("<!DOCTYPE");
    // Non-JSON response (e.g., 500 HTML/plain text from proxy/server)
    if (!response.ok) {
      if (response.status === 500 || response.status === 502 || response.status === 503 || response.status === 504) {
        throw new ApiError(
          "Media Downloader backend server is currently unreachable. Please ensure the backend service is running and accessible.",
          "BACKEND_UNAVAILABLE",
          response.status,
          true
        );
      }
      if (response.status === 404) {
        throw new ApiError(
          `API endpoint not found (404) at ${response.url}. Please verify that the backend API URL is configured properly.`,
          "ENDPOINT_NOT_FOUND",
          404,
          false
        );
      }
      throw new ApiError(
        `Server responded with error (${response.status}): ${text.slice(0, 100) || response.statusText}`,
        "SERVER_ERROR",
        response.status,
        false
      );
    }

    if (isHtml) {
      throw new ApiError(
        "The server returned an HTML page instead of API JSON data. Please verify that your backend API server is online and that NEXT_PUBLIC_API_URL is properly configured.",
        "INVALID_RESPONSE",
        response.status,
        true,
        "Verify that your backend server (e.g. Render or local port 8000) is online and accepting requests."
      );
    }

    throw new ApiError("Received invalid response from server.", "INVALID_RESPONSE", response.status);
  }

  if (!response.ok) {
    const errorObj = data?.error;
    const errorMsg =
      errorObj?.message ||
      data?.detail ||
      data?.error_message ||
      data?.message ||
      `Request failed with status ${response.status}`;
    const errorCode = errorObj?.code || data?.error_code || "REQUEST_FAILED";
    const retryable =
      errorObj?.retryable !== undefined
        ? errorObj.retryable
        : response.status === 429 || response.status === 504;
    const userAction = errorObj?.userAction || data?.user_action;
    const jobId = data?.job_id;
    throw new ApiError(errorMsg, errorCode, response.status, retryable, userAction, jobId);
  }

  return data as T;
}

/**
 * Resolves the backend API base URL dynamically at runtime.
 * Prioritizes:
 * 1. Runtime window/document override (window.__API_BASE_URL__ or <meta name="api-base-url" content="...">)
 * 2. Inlined NEXT_PUBLIC_API_URL environment variable
 * 3. Browser localhost/127.0.0.1 loopback detection
 * 4. Production Render fallback: https://the-downloader-nlb5.onrender.com
 */
export function getApiBaseUrl(): string {
  // 1. Runtime window or meta tag override (enables shared hosting / cPanel override without rebuild)
  if (typeof window !== "undefined") {
    const win = window as any;
    if (win.__API_BASE_URL__ && typeof win.__API_BASE_URL__ === "string" && win.__API_BASE_URL__.trim()) {
      return win.__API_BASE_URL__.trim().replace(/\/+$/, "");
    }
    try {
      const meta = document.querySelector('meta[name="api-base-url"]');
      if (meta) {
        const content = meta.getAttribute("content");
        if (content && content.trim() && !content.includes("__API_BASE_URL__")) {
          return content.trim().replace(/\/+$/, "");
        }
      }
    } catch {
      // DOM access fallback
    }
  }

  // 2. Next.js inlined environment variable
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (envUrl && typeof envUrl === "string" && envUrl.trim() && envUrl !== "undefined" && envUrl !== "null") {
    let url = envUrl.trim().replace(/\/+$/, "");
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      url = url.includes("localhost") || url.includes("127.0.0.1") ? `http://${url}` : `https://${url}`;
    }
    return url;
  }

  // 3. Localhost / loopback browser detection
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    if (hostname === "localhost" || hostname === "127.0.0.1" || hostname === "0.0.0.0") {
      return "http://127.0.0.1:8000";
    }
  }

  // 4. Default production backend
  return "https://the-downloader-nlb5.onrender.com";
}

export const API_BASE_URL = "https://the-downloader-nlb5.onrender.com";

export async function extractMedia(url: string): Promise<ExtractionResult> {
  const baseUrl = getApiBaseUrl();
  try {
    const response = await fetch(`${baseUrl}/api/extract`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    const data = await handleResponse<{ success: boolean; media: ExtractionResult }>(response);
    if (!data.success || !data.media) {
      throw new ApiError("Failed to extract media details from this URL.", "EXTRACTION_FAILED");
    }
    return data.media;
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      err.message || "Failed to connect to media extraction service.",
      "CONNECTION_ERROR"
    );
  }
}

export async function createJob(request: CreateJobRequest): Promise<{ job_id: string }> {
  const baseUrl = getApiBaseUrl();
  try {
    const response = await fetch(`${baseUrl}/api/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    const data = await handleResponse<{ success: boolean; job_id: string }>(response);
    if (!data.success || !data.job_id) {
      throw new ApiError("Failed to schedule download job.", "JOB_CREATION_FAILED");
    }
    return { job_id: data.job_id };
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      err.message || "Failed to connect to job service.",
      "CONNECTION_ERROR"
    );
  }
}

export async function cancelJob(jobId: string): Promise<void> {
  const baseUrl = getApiBaseUrl();
  try {
    const response = await fetch(`${baseUrl}/api/jobs/${jobId}/cancel`, {
      method: "POST",
    });
    await handleResponse<{ success: boolean }>(response);
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(err.message || "Could not cancel job.", "CANCEL_FAILED");
  }
}

export async function getJobStatus(jobId: string): Promise<JobProgressEvent> {
  const baseUrl = getApiBaseUrl();
  const response = await fetch(`${baseUrl}/api/jobs/${jobId}`);
  return handleResponse<JobProgressEvent>(response);
}
