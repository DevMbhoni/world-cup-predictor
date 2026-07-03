import { useState } from "react";
import { Activity, BarChart3, ShieldCheck, Trophy, Users } from "lucide-react";
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
      {activePage === "dashboard" && <Dashboard onOpenPage={setActivePage} />}
      {activePage === "predictor" && <MatchPredictor />}
      {activePage === "tournament" && <TournamentPage />}
      {activePage === "bracket" && <BracketPage />}
      {activePage === "golden-boot" && <GoldenBootPage />}
      {activePage === "rankings" && <RankingsPage />}
    </AppShell>
  );
}

function Dashboard({ onOpenPage }: { onOpenPage: (page: PageKey) => void }) {
  return (
    <div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={<Users size={20} />}
          label="Teams"
          value="48"
          description="Qualified teams"
          accent="sky"
        />
        <StatCard
          icon={<Trophy size={20} />}
          label="Tournament"
          value="104"
          description="Total matches"
          accent="gold"
        />
        <StatCard
          icon={<BarChart3 size={20} />}
          label="Models"
          value="4"
          description="Classifier, scoreline, markets, simulation"
          accent="blue"
        />
        <StatCard
          icon={<ShieldCheck size={20} />}
          label="Status"
          value="Live"
          description="Updated tournament state"
          accent="red"
        />
      </div>

      <div className="mt-8 grid gap-5 lg:grid-cols-2">
        <FeatureCard
          title="Predict a match"
          description="Select two teams and view final outcome probability, expected goals, scorelines, and markets."
          buttonLabel="Open predictor"
          onClick={() => onOpenPage("predictor")}
        />
        <FeatureCard
          title="View tournament bracket"
          description="Track completed matches and view projected paths through the knockout bracket."
          buttonLabel="Open bracket"
          onClick={() => onOpenPage("bracket")}
        />
        <FeatureCard
          title="Tournament simulation"
          description="See which teams are most likely to reach each round and win the tournament."
          buttonLabel="Open tournament"
          onClick={() => onOpenPage("tournament")}
        />
        <FeatureCard
          title="Golden Boot race"
          description="View top scorer probabilities using the Monte Carlo Golden Boot simulation."
          buttonLabel="Open Golden Boot"
          onClick={() => onOpenPage("golden-boot")}
        />
      </div>
    </div>
  );
}

type StatCardProps = {
  icon: React.ReactNode;
  label: string;
  value: string;
  description: string;
  accent: "sky" | "gold" | "blue" | "red";
};

function StatCard({ icon, label, value, description, accent }: StatCardProps) {
  const accentClasses = {
    sky: "bg-sky-50 text-sky-700 border-sky-200",
    gold: "bg-amber-50 text-amber-700 border-amber-200",
    blue: "bg-blue-50 text-blue-700 border-blue-200",
    red: "bg-red-50 text-red-700 border-red-200",
  };

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">{label}</p>
        <div className={`rounded-2xl border p-2.5 ${accentClasses[accent]}`}>
          {icon}
        </div>
      </div>
      <p className="mt-6 text-4xl font-semibold text-slate-950">{value}</p>
      <p className="mt-2 text-sm text-slate-500">{description}</p>
    </div>
  );
}

function FeatureCard({
  title,
  description,
  buttonLabel,
  onClick,
}: {
  title: string;
  description: string;
  buttonLabel: string;
  onClick: () => void;
}) {
  return (
    <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="text-2xl font-semibold text-slate-950">{title}</h3>
      <p className="mt-3 leading-6 text-slate-600">{description}</p>
      <button
        type="button"
        onClick={onClick}
        className="mt-6 rounded-2xl bg-sky-600 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-sky-500"
      >
        {buttonLabel}
      </button>
    </div>
  );
}

export default App;