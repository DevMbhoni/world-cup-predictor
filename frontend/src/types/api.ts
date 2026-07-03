export type Team = {
    team_id: number;
    team_name: string;
    confederation?: string;
    group_name?: string;
    fifa_ranking?: number;
    elo_rating?: number;
};

export type TeamsResponse = {
    source_file: string;
    count: number;
    results: Team[];
};

export type PredictionResult = {
    match: {
        home_team: string;
        away_team: string;
    };
    final_prediction: {
        result: "HOME_WIN" | "DRAW" | "AWAY_WIN";
        confidence: "Low" | "Medium" | "High";
        probability: number;
        probability_percent: number;
        probabilities: {
            home_win: number;
            draw: number;
            away_win: number;
        };
        probabilities_percent: {
            home_win: number;
            draw: number;
            away_win: number;
        };
        blend: {
            classifier_weight: number;
            poisson_weight: number;
        };
    };
    model_agreement: {
        agree: boolean;
        classifier_prediction: string;
        poisson_prediction: string;
        final_prediction: string;
        message: string;
    };
    scoreline_model: {
        prediction: string;
        expected_goals: {
            home: number;
            away: number;
        };
        top_scorelines: {
            home_score: number;
            away_score: number;
            scoreline: string;
            probability: number;
            probability_percent: number;
        }[];
        probabilities_percent: {
            home_win: number;
            draw: number;
            away_win: number;
        };
    };
    markets: {
        poisson_percent: {
            over_1_5: number;
            over_2_5: number;
            over_3_5: number;
            both_teams_score: number;
            home_clean_sheet: number;
            away_clean_sheet: number;
        };
    };
};

export type MatchPredictionResponse = {
    home_team: string;
    away_team: string;
    prediction: PredictionResult;
};

export type TournamentTeamSimulation = {
    team_id: number;
    team: string;
    status: "Active" | "Eliminated" | "Not qualified for knockouts" | string;
    winner_probability: number;
    final_probability: number;
    semi_final_probability: number;
    quarter_final_probability: number;
    round_of_16_probability: number;
    round_of_32_probability: number;
};

export type TournamentSimulationResponse = {
    source_file: string;
    count: number;
    results: TournamentTeamSimulation[];
};

export type GoldenBootPlayer = {
    player_id: number;
    player_name: string;
    team_id: number;
    team_name: string;
    position: string;
    current_goals: number;
    expected_final_goals: number;
    golden_boot_probability: number;
    top_3_probability: number;
    scoring_weight: number;
    minutes_played: number;
    matches_started: number;
    shots: number;
    shots_on_target: number;
};

export type GoldenBootSimulationResponse = {
    model_type: string;
    source_file: string;
    count: number;
    results: GoldenBootPlayer[];
};

export type TeamRanking = {
    elo_rank?: number;
    team: string;
    elo_rating: number;
    date?: string;
};

export type TeamRankingsResponse = {
    source_file: string;
    count: number;
    results: TeamRanking[];
};

export type BracketTeam = {
    team_id: number | null;
    team_name: string | null;
    is_confirmed?: boolean;
    projection?: {
        team_id: number | null;
        team_name: string | null;
    } | null;
    score: number | null;
    source?: {
        source_match_id: number | null;
        source_type: string | null;
        label: string | null;
    } | null;
    probabilities?: {
        status?: string;
        winner_probability?: number;
        final_probability?: number;
        semi_final_probability?: number;
        quarter_final_probability?: number;
        round_of_16_probability?: number;
        round_of_32_probability?: number;
    };
};

export type BracketMatch = {
    match_id: number;
    stage_id: number;
    stage_name: string;
    date: string | null;
    kickoff_time_utc: string | null;
    venue_id: number | null;
    status: string;
    is_completed: boolean;
    home_team: BracketTeam;
    away_team: BracketTeam;
    winner: {
        team_id: number | null;
        team_name: string | null;
        is_projected: boolean;
    };
    loser: {
        team_id: number | null;
        team_name: string | null;
        is_projected: boolean;
    };
};

export type BracketResponse = {
    source_files: {
        live_matches: string;
        bracket: string;
        teams: string;
        simulation: string;
    };
    count: number;
    matches: BracketMatch[];
    grouped_by_stage: Record<string, BracketMatch[]>;
};