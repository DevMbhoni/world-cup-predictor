import { apiClient } from "./client";
import type { TeamsResponse } from "../types/api";

export async function getTeams(): Promise<TeamsResponse> {
    const response = await apiClient.get<TeamsResponse>("/api/v1/teams");
    return response.data;
}