import { ExtractionResult, CreateJobRequest, JobProgressEvent } from "../types/media";

export class ApiError extends Error {
  code: string;
  status?: number;

  constructor(message: string, code: string = "REQUEST_FAILED", status?: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
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
          "Media Downloader backend server is currently unreachable. Please ensure the backend API is running on port 8000.",
          "BACKEND_UNAVAILABLE",
          response.status
        );
      }
      throw new ApiError(
        `Server responded with error (${response.status}): ${text.slice(0, 100) || response.statusText}`,
        "SERVER_ERROR",
        response.status
      );
    }
    throw new ApiError("Received invalid response from server.", "INVALID_RESPONSE", response.status);
  }

  if (!response.ok) {
    const errorMsg = data?.detail || data?.error_message || data?.message || `Request failed with status ${response.status}`;
    const errorCode = data?.error_code || "REQUEST_FAILED";
    throw new ApiError(errorMsg, errorCode, response.status);
  }

  return data as T;
}

export async function extractMedia(url: string): Promise<ExtractionResult> {
  try {
    const response = await fetch("/api/extract", {
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
    const response = await fetch("/api/jobs", {
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
    const response = await fetch(`/api/jobs/${jobId}/cancel`, {
      method: "POST",
    });
    await handleResponse<{ success: boolean }>(response);
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(err.message || "Could not cancel job.", "CANCEL_FAILED");
  }
}

export async function getJobStatus(jobId: string): Promise<JobProgressEvent> {
  const response = await fetch(`/api/jobs/${jobId}`);
  return handleResponse<JobProgressEvent>(response);
}
