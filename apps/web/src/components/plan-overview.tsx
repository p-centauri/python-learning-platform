import Link from "next/link";
import { ArrowRight } from "lucide-react";
import type { PersonalPlanResponse } from "@/lib/types";
export function PlanOverview({ data }: { data: PersonalPlanResponse }) {
  const next = data.plan?.items[0];
  return (
    <section
      className="panel plan-overview"
      aria-label="Personal learning plan"
    >
      <div>
        <p className="overline">YOUR PERSONAL PLAN</p>
        <h2>
          {next?.title ??
            (data.plan
              ? "Your study queue is clear"
              : "Make room for your next skill")}
        </h2>
        <p>
          {next?.reason ??
            (data.plan
              ? "Explore project work or check your plan for review recommendations."
              : "Choose your goal and weekly study time to get a plan that fits you.")}
        </p>
        {data.plan && (
          <small className="muted">
            {data.plan.goal_title} · {data.preferences?.weekly_hours} hours per
            week
          </small>
        )}
      </div>
      <div className="plan-overview-links">
        {next && (
          <Link className="button primary" href={next.href}>
            Start next action <ArrowRight size={16} />
          </Link>
        )}
        <Link className="button secondary" href="/plan">
          {data.plan ? "View or edit my plan" : "Create my learning plan"}
          <ArrowRight size={16} />
        </Link>
      </div>
    </section>
  );
}
