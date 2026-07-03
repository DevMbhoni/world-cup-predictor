import { apiClient } from "./client";
import type { MatchPredictionResponse } from "../types/api";

export async function predictMatch(
    homeTeam: string,
    awayTeam: string
): Promise<MatchPredictionResponse> {
    const response = await apiClient.get<MatchPredictionResponse>(
        "/api/v1/matches/predict",
        {
            params: {
                home_team: homeTeam,
                away_team: awayTeam,
            },
        }
    );

    return response.data;
}