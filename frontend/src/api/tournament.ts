import { apiClient } from "./client";
import type {
    BracketResponse,
    TournamentSimulationResponse,
} from "../types/api";

export async function getTournamentSimulation(
    limit = 25
): Promise<TournamentSimulationResponse> {
    const response = await apiClient.get<TournamentSimulationResponse>(
        "/api/v1/tournament/live-simulation",
        {
            params: {
                limit,
            },
        }
    );

    return response.data;
}

export async function getTournamentBracket(): Promise<BracketResponse> {
    const response = await apiClient.get<BracketResponse>(
        "/api/v1/tournament/bracket"
    );

    return response.data;
}