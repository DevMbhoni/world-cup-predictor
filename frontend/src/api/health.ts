import { apiClient } from "./client";

export type HealthResponse = {
    status?: string;
    message?: string;
};

export async function getApiHealth(): Promise<HealthResponse> {
    const response = await apiClient.get<HealthResponse>("/health");
    return response.data;
}