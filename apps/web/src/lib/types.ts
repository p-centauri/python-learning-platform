export type User = { id: number; name: string; email: string };
export type Lesson = {
  id: string;
  title: string;
  summary: string;
  track_id: string;
  module_id: string;
  skill: string;
  minutes: number;
  prerequisites: string[];
  objectives: string[];
  completed?: boolean;
  reading: string[];
  exercise_count: number;
};
export type Track = {
  id: string;
  title: string;
  description: string;
  topics: string[];
  optional: boolean;
};
export type Curriculum = {
  version: string;
  tracks: Track[];
  modules: {
    id: string;
    track_id: string;
    title: string;
    description?: string;
    project_id?: string;
  }[];
  lessons: Lesson[];
};
export type Exercise = {
  id: string;
  title: string;
  kind: string;
  difficulty: string;
  prompt: string;
  options: string[];
};
export type Attempt = {
  id: number;
  answer: number;
  score: number;
  hints_used: number;
  is_review: boolean;
  created_at: string;
};
export type ExerciseDetail = Exercise & {
  lesson_id: string;
  skill: string;
  hints: string[];
  revealed: boolean;
  solution: string | null;
  attempts: Attempt[];
};
export type LessonDetail = Lesson & {
  body: string;
  exercises: Exercise[];
  note: string;
  bookmarked: boolean;
  completed: boolean;
  sections: { id: string; title: string }[];
  navigation: {
    previous: { id: string; title: string } | null;
    next: { id: string; title: string } | null;
    prerequisites: { id: string; title: string }[];
  };
};

export type GlossaryTerm = {
  id: string;
  term: string;
  definition: string;
  lessons: { id: string; title: string }[];
};
export type LessonCheckpoint = {
  id: string;
  kind: "predict" | "debug";
  title: string;
  prompt: string;
  code: string;
  options: string[];
};
export type CheckpointAttempt = {
  id: number;
  lesson_id: string;
  checkpoint_id: string;
  version: string;
  policy: string;
  question: LessonCheckpoint;
  answer: number;
  result: { correct: boolean; expected: string; explanation: string };
  created_at: string;
};
export type LessonActivities = {
  version: string;
  note: string;
  diagram: {
    title: string;
    steps: { label: string; detail: string }[];
    caption: string;
  };
  glossary: GlossaryTerm[];
  checkpoints: LessonCheckpoint[];
  history: CheckpointAttempt[];
  history_limit: number;
};
export type Skill = {
  skill: string;
  score: number;
  assessed: number;
  total: number;
};
export type Dashboard = {
  completed_lessons: number;
  total_lessons: number;
  attempts: number;
  solved_exercises: number;
  mastery: number;
  skills: Skill[];
  weak_skills: Skill[];
  streak: number;
  review_due: number;
  retention_due: number;
  next_lesson: Lesson;
  recent_attempts: {
    id: number;
    exercise_id: string;
    title: string;
    score: number;
    created_at: string;
  }[];
};
export type Review = {
  exercise_id: string;
  title: string;
  skill: string;
  due_at: string;
  due: boolean;
  interval_days: number;
  repetitions: number;
};
export type Project = {
  id: string;
  title: string;
  number: string;
  description: string;
  stack: string;
  lesson_id?: string;
  starter_url?: string;
  tasks: {
    id: string;
    title: string;
    description: string;
    completed: boolean;
  }[];
};

export type ProjectArtifact = {
  exam_evidence?: {
    attempt_id: number;
    exam_id: string;
    version: string;
    responses: {
      id: string;
      prompt: string;
      answer: string | number | number[];
    }[];
    source: string | null;
    objective: CodingResult | null;
  };
  repository_url: string;
  revision_ref: string;
  design_notes: string;
  evidence: string;
  test_status: "not-run" | "passed" | "failed";
  test_command: string;
  test_output: string;
  change_summary: string;
};
export type ProjectRubric = {
  version: string;
  project_title: string;
  note: string;
  criteria: { id: string; title: string; expectation: string }[];
  scale: { score: number; label: string; description: string }[];
};
export type ProjectFeedback = {
  id: number;
  kind: "self" | "human";
  reviewer_name: string;
  ratings: Record<string, { score: number; evidence: string }>;
  summary: string;
  next_steps: string;
  outcome: "meets-rubric" | "changes-requested";
  created_at: string;
};
export type ProjectSubmission = {
  id: number;
  project_id: string;
  revision: number;
  parent_id: number | null;
  status: "draft" | "submitted";
  artifact: ProjectArtifact;
  rubric: ProjectRubric;
  owner_name: string;
  is_owner: boolean;
  can_review: boolean;
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
  feedback: ProjectFeedback[];
  assignments: { id: number; email: string; active: boolean }[];
};
export type ProjectHistory = {
  project: Project;
  rubric: ProjectRubric;
  submissions: ProjectSubmission[];
};
export type ReviewInboxItem = {
  id: number;
  revision: number;
  title: string;
  owner_name: string;
  submitted_at: string;
  reviewed: boolean;
};

export type CodingResult = {
  status: "passed" | "failed";
  passed: number;
  total: number;
  checks: {
    name: string;
    public: boolean;
    status: string;
    actual: unknown;
    message: string;
  }[];
  duration_ms: number;
  profile: string;
  note: string;
};
export type CodingAttempt = {
  id: number;
  exercise_id: string;
  code: string;
  version: string;
  result: CodingResult;
  created_at: string;
};
export type RunnerStatus = {
  ready: boolean;
  message: string;
  profile: string | null;
};
export type CodingDefinition = {
  id: string;
  title: string;
  language: "python" | "sql";
  prompt: string;
  starter: string;
  lesson_id: string;
  schema: string | null;
  examples: {
    name: string;
    args?: unknown[];
    expected?: unknown;
    error?: string;
    setup_sql?: string;
    columns?: string[];
  }[];
  check_count: number;
};
export type CodingCatalog = {
  version: string;
  note: string;
  runner: RunnerStatus;
  exercises: (CodingDefinition & { attempt_count: number; passed: boolean })[];
};
export type CodingDetail = CodingDefinition & {
  version: string;
  note: string;
  code: string;
  draft_saved: boolean;
  runner: RunnerStatus;
  attempts: CodingAttempt[];
  limits: {
    runs: number;
    window_minutes: number;
    code_bytes: number;
    job_seconds: number;
  };
};
export type ExamResult = {
  score: number | null;
  correct?: number;
  total?: number;
  evaluation?: {
    label: string;
    meets_target: boolean;
    overall_target: number;
    category_target: number;
    note: string;
  };
  study_recommendations?: { skill: string; title: string; url: string }[];
  practical_followup?: string | null;
  categories: {
    skill: string;
    score: number;
    correct: number;
    total: number;
  }[];
  explanations: {
    id: string;
    correct: boolean;
    answer: number;
    explanation: string;
  }[];
  recommendations: { id: string; title: string }[];
};
export type ExamAttempt = {
  id: number;
  exam_id: string;
  title: string;
  status: string;
  answers: Record<string, number>;
  result: ExamResult | null;
  started_at: string;
  questions: {
    id: string;
    skill: string;
    prompt: string;
    options: string[];
    code?: string;
  }[];
};
export type ExamDefinition = {
  mode?: "knowledge" | "design" | "repair";
  id: string;
  title: string;
  description: string;
  minutes: number;
  level: string;
  question_count: number;
  topics: string[];
  library_note: string;
  libraries: { name: string; kind: string; expectation: string; url: string }[];
  practical_followup: string | null;
  evaluation_policy: {
    overall_target: number;
    category_target: number;
    note: string;
  } | null;
};
export type ExamCatalog = {
  exams: ExamDefinition[];
  exam: { id: string; title: string; description: string; minutes: number };
  question_count: number;
  attempts: {
    id: number;
    exam_id: string;
    title: string;
    status: string;
    result: ExamResult | null;
    started_at: string;
  }[];
};

export type LearningPreferences = {
  goal: string;
  weekly_hours: number;
  starting_mode: "recommended" | "from-start";
};
export type PlanAction = {
  kind: "lesson" | "practice" | "review";
  id: string;
  title: string;
  href: string;
  minutes: number;
  reason: string;
  lesson_id: string;
};
export type PersonalPlanResponse = {
  goals: { id: string; title: string; description: string; tracks: string[] }[];
  preferences: LearningPreferences | null;
  policy_version: string;
  catalog_version: string;
  plan: {
    goal_title: string;
    weekly_minutes: number;
    scheduled_minutes: number;
    remaining_minutes: number;
    items: PlanAction[];
    starting_point: {
      id: string;
      title: string;
      reason: string;
      prerequisites: { id: string; title: string }[];
    } | null;
    evidence: {
      id: number;
      title: string;
      score: number | null;
      submitted_at: string;
    }[];
    uncovered_topics: string[];
    route: { id: string; title: string; completed: boolean }[];
    coverage_note: string;
  } | null;
};

export type RecallEvidence = { correct: number; total: number };
export type RecallKind =
  "fresh-delayed" | "repeated-delayed" | "immediate" | "assisted";
export type RecallTopic = {
  id: string;
  title: string;
  lesson_id: string;
  skill: string;
  source_incorrect: number;
  check_incorrect: number;
  incorrect: number;
  source_questions_missed: number;
  recurring: boolean;
  last_incorrect_at: string | null;
  source_recognition: RecallEvidence;
  fresh_delayed: RecallEvidence;
  immediate: RecallEvidence;
  repeated_delayed: RecallEvidence;
  assisted: RecallEvidence;
  due_at: string | null;
  due: boolean;
  interval_days: number;
  active_id: number | null;
  unseen_questions: number;
  question_count: number;
  started: boolean;
};
export type RecallSession = {
  id: number;
  concept_id: string;
  title: string;
  version: string;
  policy: string;
  status: "active" | "submitted" | "abandoned";
  mode: "practice" | "delayed";
  fresh: boolean;
  question: {
    id: string;
    prompt: string;
    code?: string;
    format: "short-answer";
    case_sensitive: boolean;
  };
  answer: string;
  used_help: boolean;
  result: {
    correct: boolean;
    evidence_kind: RecallKind;
    expected: string;
    explanation: string;
    interval_days: number;
    next_due_at: string;
    note: string;
    observed_study?: boolean;
  } | null;
  created_at: string;
  submitted_at: string | null;
};
export type RecallOverview = {
  version: string;
  policy: string;
  note: string;
  topics: RecallTopic[];
  catalog: {
    id: string;
    title: string;
    skill: string;
    question_count: number;
  }[];
  summary: {
    due: number;
    recurring: number;
    source_recognition: RecallEvidence;
    fresh_delayed: RecallEvidence;
    immediate: RecallEvidence;
    repeated_delayed: RecallEvidence;
    assisted: RecallEvidence;
  };
};
export type RecallDetail = {
  topic: RecallTopic;
  note: string;
  sources: { id: string; title: string; href: string }[];
  active: RecallSession | null;
  history: RecallSession[];
};
