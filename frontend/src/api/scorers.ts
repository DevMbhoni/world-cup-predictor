import { apiClient } from "./client";
import type { GoldenBootSimulationResponse } from "../types/api";

export async function getGoldenBootSimulation(
    limit = 30
): Promise<GoldenBootSimulationResponse> {
    const response = await apiClient.get<GoldenBootSimulationResponse>(
        "/api/v1/scorers/golden-boot-simulation",
        {
            params: {
                limit,
            },
        }
    );

    return response.data;
}