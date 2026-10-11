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
      throw new ApiError(
        `Server responded with error (${response.status}): ${text.slice(0, 100) || response.statusText}`,
        "SERVER_ERROR",
        response.status,
        false
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

function getApiBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    let url = process.env.NEXT_PUBLIC_API_URL.trim().replace(/\/+$/, "");
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      url = url.includes("localhost") || url.includes("127.0.0.1") ? `http://${url}` : `https://${url}`;
    }
    return url;
  }
  if (typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")) {
    return "http://127.0.0.1:8000";
  }
  return "https://the-downloader-nlb5.onrender.com";
}

export const API_BASE_URL = getApiBaseUrl();

export async function extractMedia(url: string): Promise<ExtractionResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/extract`, {
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
  try {
    const response = await fetch(`${API_BASE_URL}/api/jobs`, {
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
  try {
    const response = await fetch(`${API_BASE_URL}/api/jobs/${jobId}/cancel`, {
      method: "POST",
    });
    await handleResponse<{ success: boolean }>(response);
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(err.message || "Could not cancel job.", "CANCEL_FAILED");
  }
}

export async function getJobStatus(jobId: string): Promise<JobProgressEvent> {
  const response = await fetch(`${API_BASE_URL}/api/jobs/${jobId}`);
  return handleResponse<JobProgressEvent>(response);
}
