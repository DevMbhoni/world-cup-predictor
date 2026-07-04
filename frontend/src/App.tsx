import { useState } from "react";
import {
  BarChart3,
  ShieldCheck,
  Trophy,
  Users,
} from "lucide-react";
import AppShell, { type PageKey } from "./layouts/AppShell";
import MatchPredictor from "./features/match/MatchPredictor";
import TournamentPage from "./features/tournament/TournamentPage";
import BracketPage from "./features/tournament/BracketPage";
import GoldenBootPage from "./features/scorers/GoldenBootPage";
import RankingsPage from "./features/rankings/RankingsPage";

function App() {
  const [activePage, setActivePage] = useState<PageKey>("dashboard");

  return (
    <AppShell activePage={activePage} onPageChange={setActivePage}>
      {activePage === "dashboard" && (
        <Dashboard onOpenPage={setActivePage} />
      )}

      {activePage === "predictor" && <MatchPredictor />}
      {activePage === "tournament" && <TournamentPage />}
      {activePage === "bracket" && <BracketPage />}
      {activePage === "golden-boot" && <GoldenBootPage />}
      {activePage === "rankings" && <RankingsPage />}
    </AppShell>
  );
}

function Dashboard({
  onOpenPage,
}: {
  onOpenPage: (page: PageKey) => void;
}) {
  return (
    <div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={<Users size={21} />}
          label="Teams"
          value="48"
          description="Qualified teams"
          accent="blue"
        />

        <StatCard
          icon={<Trophy size={21} />}
          label="Tournament"
          value="104"
          description="Total matches"
          accent="lime"
        />

        <StatCard
          icon={<BarChart3 size={21} />}
          label="Models"
          value="4"
          description="Classifier, scoreline, markets, simulation"
          accent="purple"
        />

        <StatCard
          icon={<ShieldCheck size={21} />}
          label="Status"
          value="Live"
          description="Updated tournament state"
          accent="red"
        />
      </div>

      <div className="mt-8 grid gap-5 lg:grid-cols-2">
        <FeatureCard
          title="Predict a match"
          description="Select two teams and inspect final outcome probabilities, expected goals, scorelines, and match markets."
          buttonLabel="Open predictor"
          accent="blue"
          onClick={() => onOpenPage("predictor")}
        />

        <FeatureCard
          title="Knockout bracket"
          description="Follow confirmed fixtures and model-projected paths through the knockout tournament."
          buttonLabel="Open bracket"
          accent="purple"
          onClick={() => onOpenPage("bracket")}
        />

        <FeatureCard
          title="Tournament simulation"
          description="Explore which teams are most likely to progress and become world champions."
          buttonLabel="Open tournament"
          accent="teal"
          onClick={() => onOpenPage("tournament")}
        />

        <FeatureCard
          title="Golden Boot race"
          description="View scorer probabilities and expected final goal totals from the Monte Carlo simulation."
          buttonLabel="Open Golden Boot"
          accent="orange"
          onClick={() => onOpenPage("golden-boot")}
        />
      </div>
    </div>
  );
}

type Accent = "blue" | "lime" | "purple" | "red";

type StatCardProps = {
  icon: React.ReactNode;
  label: string;
  value: string;
  description: string;
  accent: Accent;
};

function StatCard({
  icon,
  label,
  value,
  description,
  accent,
}: StatCardProps) {
  const styles: Record<Accent, string> = {
    blue: "bg-[#2f54eb] text-white",
    lime: "bg-[#bef20a] text-black",
    purple: "bg-[#6a00ff] text-white",
    red: "bg-[#ff2a1a] text-white",
  };

  return (
    <div className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-sm">
      <div className={`h-2 w-full ${styles[accent]}`} />

      <div className="p-5">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-slate-500">{label}</p>

          <div
            className={`rounded-2xl p-2.5 ${styles[accent]}`}
          >
            {icon}
          </div>
        </div>

        <p className="mt-6 text-4xl font-black text-black">{value}</p>

        <p className="mt-2 text-sm text-slate-500">{description}</p>
      </div>
    </div>
  );
}

type FeatureAccent = "blue" | "purple" | "teal" | "orange";

function FeatureCard({
  title,
  description,
  buttonLabel,
  accent,
  onClick,
}: {
  title: string;
  description: string;
  buttonLabel: string;
  accent: FeatureAccent;
  onClick: () => void;
}) {
  const styles: Record<
    FeatureAccent,
    {
      line: string;
      button: string;
    }
  > = {
    blue: {
      line: "bg-[#2f54eb]",
      button: "bg-[#2f54eb] text-white hover:bg-[#252b91]",
    },

    purple: {
      line: "bg-[#6a00ff]",
      button: "bg-[#6a00ff] text-white hover:bg-[#4f00c4]",
    },

    teal: {
      line: "bg-[#00e0c6]",
      button: "bg-[#00e0c6] text-black hover:bg-[#00c7b0]",
    },

    orange: {
      line: "bg-[#ff651f]",
      button: "bg-[#ff651f] text-white hover:bg-[#e94f0b]",
    },
  };

  return (
    <div className="relative overflow-hidden rounded-[2rem] border border-slate-200 bg-white p-7 shadow-sm">
      <div
        className={`absolute left-0 top-0 h-full w-2 ${styles[accent].line}`}
      />

      <h3 className="text-2xl font-black text-black">{title}</h3>

      <p className="mt-3 max-w-xl leading-7 text-slate-600">
        {description}
      </p>

      <button
        type="button"
        onClick={onClick}
        className={`mt-7 rounded-full px-5 py-3 text-sm font-semibold transition ${styles[accent].button}`}
      >
        {buttonLabel}
      </button>
    </div>
  );
}

export default App;