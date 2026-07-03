import { apiClient } from "./client";
import type { TeamRankingsResponse } from "../types/api";

export async function getTeamRankings(
    limit = 50
): Promise<TeamRankingsResponse> {
    const response = await apiClient.get<TeamRankingsResponse>(
        "/api/v1/rankings/teams",
        {
            params: {
                limit,
            },
        }
    );

    return response.data;
}