import {apiClient} from "./client";
import type { PredictionHistoryResponse } from "../types/api";

export async function getPredictionHistory(): Promise<PredictionHistoryResponse> {
    const response = await apiClient.get<PredictionHistoryResponse>(
        "/api/v1/predictions/history"
    );

    return response.data;
}