import { Link, useParams } from "react-router-dom";
import { useContributorSummary } from "../api/queries";
import { BarChart } from "../components/BarChart";
import { CalibrationBar } from "../components/CalibrationBar";
import { DateCell } from "../components/DateCell";
import { QueryBoundary } from "../components/QueryBoundary";
import { displayName } from "./Contributors";

export function ContributorSummary() {
  const { id } = useParams<{ id: string }>();
  const query = useContributorSummary(id ?? "");

  return (
    <section>
      <p>
        <Link to="/">← Contributors</Link>
      </p>
      <QueryBoundary
        query={query}
        capability="view contributor summaries"
        notFound={
          <div role="alert">
            <h1>Contributor not found</h1>
            <p>This contributor doesn't exist, or belongs to a different organization.</p>
            <Link to="/">Back to contributors</Link>
          </div>
        }
      >
        {(data) => {
          const name = displayName(data.contributor);
          const correctPct =
            data.quiz.attempts > 0
              ? Math.round((data.quiz.correct / data.quiz.attempts) * 100)
              : null;
          return (
            <>
              <h1>{name}</h1>
              <dl>
                <dt>Identity</dt>
                <dd>
                  {data.contributor.provider}:{data.contributor.external_id}
                </dd>
                <dt>Email</dt>
                <dd>{data.contributor.email ?? ""}</dd>
                <dt>Active</dt>
                <dd>{data.contributor.active ? "Yes" : "No"}</dd>
                <dt>Last event</dt>
                <dd>
                  {data.last_event_at !== null ? <DateCell value={data.last_event_at} /> : "never"}
                </dd>
              </dl>

              <h2>Events by category</h2>
              <BarChart
                data={data.events_by_category}
                ariaLabel={`Events by category for ${name}`}
              />

              <h2>Quiz</h2>
              {data.quiz.attempts === 0 ? (
                <p>No quiz attempts.</p>
              ) : (
                <>
                  <p>
                    {data.quiz.attempts} attempts, {data.quiz.correct} correct ({correctPct}%)
                  </p>
                  <CalibrationBar
                    attempts={data.quiz.attempts}
                    calibration={data.quiz.calibration}
                  />
                </>
              )}
            </>
          );
        }}
      </QueryBoundary>
    </section>
  );
}
