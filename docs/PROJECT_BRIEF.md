You are a senior software architect, senior backend engineer, applied AI engineer, technical educator, curriculum designer, assessment designer, and senior UI/UX product designer.

Your task is to design and build a complete, production-quality learning platform that will train me from my current software-development level into a strong:

1. Backend + AI Engineer
2. Applied AI Engineer

This must not be a superficial tutorial website. Build it as a serious engineering academy/product that teaches concepts deeply, forces active practice, measures understanding, exposes weak areas, and validates whether I can actually apply the knowledge.

The platform must combine:

* structured theory
* examples
* diagrams
* coding exercises
* debugging exercises
* architecture exercises
* tricky questions
* conceptual traps
* scenario-based questions
* production incidents
* code review exercises
* database exercises
* system-design problems
* AI engineering exercises
* quizzes
* spaced review
* progress tracking
* practical projects
* three separate comprehensive exams

The end result should be something I can realistically use for many months as my personal engineering academy.

---

# 1. PRIMARY GOAL

Build a learning application that takes me section by section through the knowledge required to become highly competent in modern backend engineering and applied AI engineering.

The application must teach not only:

"What is this?"

but also:

* Why does it exist?
* What problem does it solve?
* When should I use it?
* When should I NOT use it?
* What are the tradeoffs?
* What mistakes do developers commonly make?
* How does it behave in production?
* How does it fail?
* How can I debug it?
* How can I test it?
* How does it scale?
* How does it affect security?
* How would a senior engineer reason about it?

The goal is engineering competence, not memorization.

---

# 2. MY CURRENT BACKGROUND

Assume I already have several years of software-development experience.

I already have practical experience with:

* Vue
* JavaScript
* SQL
* PostgreSQL
* APIs
* external integrations
* cron jobs
* business workflows
* validation systems
* retry systems
* state machines
* database procedures
* asynchronous processing concepts
* outbox-style patterns
* importing/mapping external data

Therefore:

Do not waste large amounts of time teaching extremely basic programming concepts.

However, still test fundamentals because gaps may exist.

The learning path should push me toward senior-level reasoning.

---

# 3. TARGET TECHNICAL PROFILE

The final target profile is:

Senior Backend / Applied AI Engineer

with strong competence in:

* Python
* FastAPI
* Django / Django REST Framework
* PostgreSQL
* Redis
* Celery
* RabbitMQ concepts
* Docker
* Linux
* CI/CD
* cloud infrastructure
* AWS
* system design
* distributed systems
* application security
* REST API design
* async programming
* architecture
* testing
* observability
* AI/LLM APIs
* embeddings
* vector search
* pgvector
* RAG
* reranking
* tool calling
* agents
* AI security
* AI evaluation
* AI observability
* production AI architecture

Secondary technologies can include:

* React or Next.js
* TypeScript
* Go
* Kafka
* Kubernetes

But these should not distract from the main learning path.

---

# 4. CURRICULUM STRUCTURE

Organize the curriculum into major Tracks.

Each Track contains Modules.

Each Module contains Lessons.

Each Lesson should contain:

1. Learning objectives
2. Prerequisites
3. Core explanation
4. Mental model
5. Real-world example
6. Code examples
7. Common mistakes
8. Production considerations
9. Senior-engineer perspective
10. Quick knowledge check
11. Tricky questions
12. Practical exercise
13. Debugging exercise
14. Architecture/scenario exercise where relevant
15. Suggested follow-up reading
16. Mastery criteria

Do not make every lesson identical mechanically. Adapt lesson structure to the subject.

---

# 5. REQUIRED TRACKS

Create all of the following Tracks.

## TRACK A — Advanced Python

Teach:

* Python object model
* mutable vs immutable objects
* references
* scope
* closures
* decorators
* iterators
* generators
* comprehensions
* context managers
* exceptions
* custom exceptions
* dataclasses
* typing
* TypeVar
* generics
* Protocol
* abstract classes
* composition
* inheritance
* dependency injection
* modules
* packages
* virtual environments
* packaging
* pyproject.toml
* logging
* debugging
* profiling
* memory considerations
* async / await
* event loop
* concurrency
* threading
* multiprocessing
* CPU-bound vs IO-bound work

Exercises must include:

* predicting code output
* identifying subtle bugs
* refactoring poor Python
* async bugs
* race conditions
* exception handling mistakes
* typing exercises
* performance exercises

---

## TRACK B — Backend Engineering with FastAPI

Teach deeply:

* FastAPI architecture
* routing
* dependencies
* dependency injection
* Pydantic
* validation
* request lifecycle
* middleware
* authentication
* authorization
* async endpoints
* background work
* SQLAlchemy
* Alembic
* repository pattern
* service layer
* domain layer
* error handling
* pagination
* filtering
* API versioning
* OpenAPI
* rate limiting
* file uploads
* webhooks
* WebSockets
* idempotency
* structured logging
* configuration
* secrets

Students must build real endpoints, not toy examples.

---

## TRACK C — Django and Django REST Framework

Teach:

* Django architecture
* ORM
* migrations
* managers
* querysets
* signals
* middleware
* authentication
* permissions
* admin
* DRF serializers
* viewsets
* generic views
* pagination
* filtering
* throttling
* authentication
* permissions
* testing
* Celery integration
* performance
* avoiding N+1 queries

Compare FastAPI and Django.

Teach when each is more appropriate.

---

## TRACK D — PostgreSQL Mastery

This should be one of the strongest sections.

Teach:

* relational modeling
* normalization
* denormalization
* primary keys
* foreign keys
* constraints
* indexes
* B-tree
* GIN
* GiST
* BRIN
* composite indexes
* covering indexes
* partial indexes
* expressions indexes
* EXPLAIN
* EXPLAIN ANALYZE
* query planner
* joins
* CTEs
* recursive CTEs
* window functions
* materialized views
* JSONB
* transactions
* ACID
* MVCC
* isolation levels
* locking
* deadlocks
* SELECT FOR UPDATE
* SKIP LOCKED
* advisory locks
* connection pooling
* partitioning
* replication concepts
* vacuum
* autovacuum
* WAL
* query optimization
* schema design
* migrations
* PostgreSQL security

Include exercises where I must diagnose slow queries using execution plans.

Include concurrency problems.

Include deadlock simulations.

Include worker-queue patterns using:

SELECT ... FOR UPDATE SKIP LOCKED

---

# 6. API AND HTTP ENGINEERING TRACK

Teach HTTP properly.

Include:

* HTTP lifecycle
* TCP basics relevant to HTTP
* DNS basics
* HTTP/1.1
* HTTP/2 concepts
* HTTP/3 concepts
* TLS
* GET
* POST
* PUT
* PATCH
* DELETE
* OPTIONS
* HEAD
* status codes
* headers
* cookies
* caching
* ETags
* CORS
* REST principles
* idempotency
* pagination
* cursor pagination
* rate limits
* retries
* exponential backoff
* jitter
* connection timeouts
* read timeouts
* circuit breakers
* webhooks
* API versioning
* API contracts
* OpenAPI
* OAuth 2
* OpenID Connect
* JWT
* API keys

Create tricky API-design exercises.

Example:

A client submits a payment request and times out before receiving the response.

How should the system behave if the same request is sent again?

---

# 7. SOFTWARE ARCHITECTURE TRACK

Teach:

* SOLID
* DRY
* KISS
* YAGNI
* cohesion
* coupling
* dependency inversion
* interfaces
* composition
* Clean Architecture
* Hexagonal Architecture
* Ports and Adapters
* Repository pattern
* Unit of Work
* Service Layer
* Domain Layer
* Domain Driven Design fundamentals
* CQRS
* event-driven architecture
* modular monolith
* microservices
* event sourcing concepts
* Saga
* outbox pattern
* inbox pattern
* idempotent consumers
* circuit breaker
* retry pattern
* bulkhead
* dead-letter queues

Do not teach patterns as dogma.

For every pattern explain:

* problem solved
* advantages
* disadvantages
* inappropriate use cases
* simpler alternatives

Include architecture smell exercises.

Show overengineered systems and ask me to simplify them.

---

# 8. DISTRIBUTED SYSTEMS TRACK

This must be challenging.

Teach:

* distributed-system fundamentals
* partial failure
* network unreliability
* timeouts
* retries
* duplicate messages
* message ordering
* eventual consistency
* strong consistency
* at-most-once
* at-least-once
* effectively-once processing
* idempotency
* distributed transactions
* two-phase commit concepts
* Saga
* outbox
* consensus concepts
* leader election concepts
* distributed locks
* race conditions
* clock problems
* CAP theorem
* backpressure
* load shedding
* batching
* replication
* sharding
* partitioning
* failure recovery

Create failure scenarios such as:

A worker writes successfully to PostgreSQL and crashes before acknowledging the queue message.

Ask me:

* what happens?
* can the event be processed twice?
* how do we make it safe?
* where should idempotency live?

---

# 9. REDIS, QUEUES, AND ASYNCHRONOUS PROCESSING

Teach:

Redis:

* strings
* hashes
* sets
* sorted sets
* TTL
* caching
* cache invalidation
* sessions
* rate limiting
* locks
* atomic operations
* pub/sub
* Streams concepts

Queues:

* Celery
* RabbitMQ
* acknowledgements
* retries
* dead-letter queues
* worker scaling
* scheduled jobs
* visibility concepts
* poison messages
* idempotent consumers

Later introduce:

* Kafka fundamentals
* partitions
* consumer groups
* offsets
* retention
* ordering

---

# 10. TESTING TRACK

Make this extensive.

Teach:

* unit tests
* integration tests
* functional tests
* end-to-end tests
* contract tests
* regression tests
* property-based testing
* load testing
* chaos concepts
* mocks
* fakes
* stubs
* fixtures
* pytest
* async tests
* database tests
* API tests
* testcontainers concepts
* coverage
* mutation testing concepts

Teach how to decide what NOT to mock.

Create broken tests and misleading tests that I must fix.

---

# 11. PRODUCTION ENGINEERING TRACK

Teach:

* Linux basics
* processes
* signals
* ports
* sockets
* filesystem
* permissions
* environment variables
* logs
* process management
* Nginx
* reverse proxy
* Docker
* Dockerfiles
* images
* layers
* Docker Compose
* container networking
* volumes
* secrets
* health checks
* graceful shutdown
* deployment
* rollbacks
* migrations
* zero-downtime concepts

CI/CD:

* Git
* branching strategies
* GitHub Actions
* linting
* tests
* builds
* security scans
* deployment pipelines

---

# 12. OBSERVABILITY TRACK

Teach the three major pillars:

* logs
* metrics
* traces

Teach:

* structured logging
* correlation IDs
* trace IDs
* OpenTelemetry concepts
* Prometheus concepts
* Grafana concepts
* alerting
* SLOs
* SLIs
* error budgets
* latency percentiles
* p50
* p95
* p99

Include production incidents where I must determine what telemetry is missing.

---

# 13. CLOUD / AWS TRACK

Teach cloud concepts before vendor-specific services.

Then teach AWS around:

* IAM
* VPC
* EC2
* S3
* RDS
* ElastiCache
* ECS
* ECR
* SQS
* SNS
* CloudWatch
* Secrets Manager
* Application Load Balancer
* Auto Scaling
* Route 53
* CloudFront concepts
* Lambda concepts

Teach:

* networking
* availability zones
* regions
* scaling
* fault tolerance
* backup
* disaster recovery
* security
* cost awareness

Do not turn the course into an AWS certification memorization guide.

---

# 14. APPLICATION SECURITY TRACK

Teach:

* OWASP Top 10
* SQL injection
* XSS
* CSRF
* SSRF
* command injection
* authentication
* authorization
* RBAC
* ABAC concepts
* password storage
* hashing
* encryption
* HTTPS
* cookies
* JWT risks
* secret management
* API security
* rate limiting
* input validation
* security headers
* dependency vulnerabilities
* supply-chain concerns

Include vulnerable applications that I must repair.

---

# 15. SYSTEM DESIGN TRACK

Teach progressively.

Examples:

* URL shortener
* notification system
* job queue
* payment service
* chat application
* file-storage service
* analytics pipeline
* rate limiter
* API gateway
* e-commerce backend
* document-processing system
* AI assistant
* financial assistant

Teach:

* requirements gathering
* functional requirements
* non-functional requirements
* traffic estimation
* storage estimation
* API design
* data modeling
* caching
* queues
* load balancing
* partitioning
* replication
* availability
* consistency
* monitoring
* failure modes
* cost

Require diagrams.

---

# 16. LLM FUNDAMENTALS TRACK

Teach applied concepts including:

* tokens
* tokenization
* context windows
* transformer concepts
* attention intuition
* embeddings
* model inference
* model families
* reasoning models
* temperature
* top-p
* sampling
* deterministic vs nondeterministic output
* hallucinations
* structured outputs
* system/user/developer instructions
* prompt design
* context engineering
* fine-tuning
* when fine-tuning is appropriate
* model selection
* latency
* token costs
* privacy
* model limits

Do not require research-level mathematics, but provide optional deeper material.

---

# 17. EMBEDDINGS AND VECTOR SEARCH TRACK

Teach:

* embedding concepts
* vector representations
* dimensions
* similarity
* cosine similarity
* dot product
* Euclidean distance
* semantic search
* vector indexing
* approximate nearest neighbor concepts
* chunking
* overlap
* metadata filtering
* hybrid search
* keyword search
* BM25 concepts
* reranking

Use PostgreSQL + pgvector as the primary implementation.

Include experiments demonstrating why poor chunking creates poor retrieval.

---

# 18. RAG TRACK

Make this one of the deepest AI sections.

Teach progressively:

Basic:

Question
→ embedding
→ retrieval
→ context
→ LLM

Advanced:

Question
→ classification
→ query rewriting
→ metadata filters
→ hybrid search
→ vector retrieval
→ reranking
→ context construction
→ generation
→ citations
→ verification

Teach:

* ingestion
* parsing
* chunking
* embedding
* indexing
* retrieval
* reranking
* context construction
* citations
* freshness
* access control
* multi-tenant RAG
* evaluation
* hallucination prevention

Create intentionally bad RAG systems that I must diagnose.

---

# 19. TOOL CALLING TRACK

Teach how LLMs interact with application functions.

Examples:

get_transactions()

create_expense()

get_weather()

send_invoice()

search_documents()

Teach:

* tool schemas
* argument validation
* retries
* authorization
* tool selection
* deterministic workflows
* structured responses
* tool errors
* tool output injection
* human approval
* auditability

Include exercises where the LLM selects the wrong tool or malformed arguments and I must fix the architecture.

---

# 20. AGENT ENGINEERING TRACK

Teach agents only after tool calling.

Teach:

* agent loop
* planning
* execution
* observation
* memory concepts
* state management
* tools
* permissions
* checkpoints
* human-in-the-loop
* workflow vs agent
* deterministic vs agentic systems
* multi-agent concepts
* limits
* budgets
* stopping conditions

Strongly emphasize:

Do not use an agent when a deterministic workflow is sufficient.

Create exercises asking whether an agent is appropriate.

---

# 21. AI SECURITY TRACK

Teach:

* prompt injection
* indirect prompt injection
* data exfiltration
* malicious documents
* tool abuse
* privilege escalation
* insecure tool calls
* sensitive-information leakage
* malicious URLs
* unsafe autonomous actions
* data isolation
* tenant isolation

Create adversarial exercises.

---

# 22. AI EVALUATION TRACK

This must be a major section.

Teach:

* why manual "looks good" evaluation is insufficient
* evaluation datasets
* golden datasets
* retrieval metrics
* answer correctness
* groundedness
* faithfulness
* hallucination measurement
* tool-selection accuracy
* argument accuracy
* latency
* token usage
* cost
* user satisfaction
* regression testing
* model comparisons
* A/B testing concepts
* LLM-as-judge limitations
* human evaluation

Create evaluation pipelines.

Require tests before changing AI prompts or retrieval logic.

---

# 23. AI OBSERVABILITY TRACK

Teach how to trace:

User request
→ prompt
→ retrieval
→ documents
→ reranker
→ LLM
→ tool
→ output
→ final response

Track:

* model
* tokens
* cost
* latency
* prompt version
* retrieved documents
* tool calls
* failures
* quality metrics

Teach debugging of AI systems.

---

# 24. OPTIONAL ML FOUNDATIONS

Provide a secondary optional path covering:

* statistics
* probability
* linear algebra
* gradient descent intuition
* supervised learning
* unsupervised learning
* classification
* regression
* overfitting
* validation
* train/test split
* neural-network basics
* PyTorch basics
* transformer architecture deeper dive

This should be optional rather than blocking the main Applied AI path.

---

# 25. EXERCISE SYSTEM

Every major Module should have several exercise categories.

Do not reuse questions with slightly different wording.

Create genuinely different exercises.

Use categories such as:

### Conceptual

Ask me to explain concepts.

### Prediction

Show code and ask what happens.

### Debugging

Give broken code and require diagnosis.

### Code Review

Provide working but poor code.

Ask me to identify:

* correctness problems
* maintainability problems
* security problems
* performance problems
* race conditions
* architectural problems

### Implementation

Ask me to implement something.

### Refactoring

Provide badly structured code.

### Database

Require SQL queries, indexing decisions, execution-plan analysis, locking decisions.

### Architecture

Give requirements and ask me to design the solution.

### Incident Response

Example:

"After a deployment, p99 latency increased from 200ms to 4 seconds."

Provide logs and metrics.

Ask me to investigate.

### Tradeoff Questions

Example:

"Redis cache or PostgreSQL query optimization?"

### Tricky Questions

Questions should target misconceptions.

Do not make them trivia.

### What Happens If?

Examples:

* What happens if the worker crashes here?
* What happens if the HTTP response is lost?
* What happens if two processes run simultaneously?
* What happens if Redis goes down?
* What happens if the same message arrives twice?

### Senior-Level Scenarios

Give incomplete requirements.

Force me to ask the right questions before designing the solution.

---

# 26. DIFFICULTY LEVELS

Every exercise should be labeled:

* Foundation
* Intermediate
* Advanced
* Senior
* Expert

Do not unlock Advanced/Senior content only based on completion.

Use mastery scores.

---

# 27. HINT SYSTEM

Exercises should support progressive hints.

Example:

Hint 1:
Conceptual direction.

Hint 2:
More specific.

Hint 3:
Nearly gives the technique but not the answer.

Do not immediately reveal solutions.

---

# 28. SOLUTION SYSTEM

Solutions should include:

* correct answer
* explanation
* reasoning
* alternative approaches
* common wrong answers
* why those answers are wrong
* production considerations

For coding problems, provide:

* reference implementation
* tests
* complexity discussion
* possible improvements

---

# 29. THREE COMPREHENSIVE EXAMS

Build THREE completely different comprehensive exams.

Do not simply randomize the same questions.

Each exam must test knowledge differently.

---

## EXAM 1 — ENGINEERING KNOWLEDGE EXAM

Purpose:

Validate theoretical and conceptual understanding.

Include:

* multiple choice
* multiple-response
* short answer
* tricky conceptual questions
* code prediction
* database reasoning
* architecture questions
* HTTP questions
* Python questions
* distributed systems
* AI concepts
* RAG
* tool calling
* security

Approximate duration:

2–3 hours.

Do not show answers while taking the exam.

Generate a score by category.

Example report:

Python: 84%
PostgreSQL: 92%
Distributed Systems: 61%
AI Engineering: 78%
Security: 54%

Then generate:

* strengths
* weaknesses
* lessons to revisit
* recommended exercises

---

## EXAM 2 — PRACTICAL ENGINEERING EXAM

Purpose:

Determine whether I can actually build and debug systems.

Give me a partially implemented application containing intentional problems.

Include issues such as:

* SQL performance issue
* N+1 query
* missing transaction
* race condition
* duplicate event handling
* retry bug
* missing idempotency
* insecure API
* poor architecture
* broken async behavior
* Docker configuration issue
* inefficient cache
* missing observability
* failing tests
* AI retrieval problem
* hallucination problem
* tool-calling validation problem

I should repair the system.

Automated tests should validate much of my work.

Also evaluate architecture decisions manually using rubrics.

Approximate duration:

4–6 hours.

---

## EXAM 3 — SENIOR SYSTEM DESIGN + APPLIED AI EXAM

Purpose:

Determine whether I can reason like a senior Backend + Applied AI Engineer.

Give me a realistic company problem.

Example:

Build a multi-tenant enterprise AI assistant that:

* supports millions of documents
* respects user permissions
* integrates with company APIs
* executes approved actions
* provides citations
* prevents cross-tenant data leakage
* handles retries
* handles duplicate events
* maintains audit logs
* controls AI costs
* measures quality
* provides observability

Require me to design:

* requirements
* architecture
* API
* database schema
* caching
* queues
* RAG pipeline
* tool architecture
* permission model
* security
* deployment
* scaling
* monitoring
* evaluation
* disaster recovery
* cost strategy

Then present follow-up problems during the exam.

Examples:

"Traffic increased 20x."

"PostgreSQL is overloaded."

"Redis is unavailable."

"The model provider has a 30-second outage."

"An attacker uploads a prompt-injection document."

"A tool was executed twice."

"The vector search returns irrelevant documents."

I must adapt my design.

Approximate duration:

3–5 hours.

Evaluate using a detailed senior-engineering rubric.

---

# 30. KNOWLEDGE GRAPH / PREREQUISITES

Create a dependency graph.

Example:

Python async
↓
FastAPI async
↓
Workers
↓
Distributed processing

SQL
↓
PostgreSQL
↓
Transactions
↓
Locks
↓
Distributed consistency

LLM fundamentals
↓
Embeddings
↓
Vector search
↓
RAG
↓
RAG evaluation

Tool calling
↓
Agents
↓
AI security

Do not allow advanced concepts to appear without introducing prerequisites.

---

# 31. PROGRESS SYSTEM

Create a proper learning-progress model.

Track:

* lessons completed
* exercises attempted
* exercises solved
* first-attempt success
* hints used
* average score
* mastery score
* weak areas
* strong areas
* review due
* projects completed
* exams completed

Show skill-level visualization.

Example:

Python              ████████░░ 82%
PostgreSQL          █████████░ 91%
Distributed Systems ██████░░░░ 63%
System Design       ███████░░░ 72%
RAG                 ████████░░ 80%
AI Evaluation       █████░░░░░ 52%

---

# 32. MASTERY MODEL

Do not treat lesson completion as mastery.

Calculate mastery using:

* quiz performance
* exercise performance
* first-attempt success
* difficulty
* hint usage
* exam results
* recent performance
* spaced-review results

A learner who watched/read everything but cannot solve problems should NOT show 100% mastery.

---

# 33. SPACED REVIEW

Add a review system.

Previously learned concepts should reappear later.

Examples:

A transaction concept from PostgreSQL may appear later in:

* payment systems
* distributed systems
* outbox
* job processing

An idempotency concept may appear later in:

* webhooks
* queues
* tool calling
* payment processing

Use spaced repetition intelligently.

---

# 34. PROJECT-BASED LEARNING

Build three major portfolio-quality projects into the curriculum.

---

## PROJECT 1 — PRODUCTION BACKEND PLATFORM

Use:

* FastAPI
* PostgreSQL
* Redis
* Celery
* Docker
* authentication
* authorization
* migrations
* background jobs
* webhooks
* idempotency
* outbox
* retries
* tests
* observability
* CI/CD

Example domain:

payment/order/commerce platform.

It should have realistic failure cases.

---

## PROJECT 2 — ENTERPRISE RAG SYSTEM

Use:

* document ingestion
* parsers
* chunking
* embeddings
* PostgreSQL
* pgvector
* hybrid retrieval
* reranking
* citations
* authorization
* multi-tenancy
* evaluation
* observability

Require measurable retrieval quality.

---

## PROJECT 3 — AI FINANCE ASSISTANT

This should be the flagship project.

Architecture:

Web/mobile client
→ API
→ AI orchestration
→ tool calling
→ PostgreSQL
→ financial analytics

Features:

* expenses
* income
* budgets
* categories
* recurring transactions
* analytics
* natural-language querying
* multilingual interface
* Uzbek
* Russian
* English
* voice-ready architecture
* structured tool calls
* permissions
* AI-generated insights
* reports
* RAG where useful
* audit logs
* evaluation
* observability

The system should never let an LLM directly mutate financial data without validated application logic.

---

# 35. USER EXPERIENCE

The UI must feel like a premium professional engineering academy.

Do NOT create a generic admin template.

Use excellent information architecture.

Main areas:

* Dashboard
* Learning Path
* Tracks
* Modules
* Lesson
* Exercises
* Playground
* Projects
* Exams
* Review
* Knowledge Map
* Progress
* Weak Areas
* Bookmarks
* Notes
* Settings

---

# 36. DASHBOARD DESIGN

Dashboard should show:

* current learning streak
* current module
* next lesson
* mastery overview
* weak skills
* review due
* project progress
* exam readiness
* recently completed exercises
* recommended next action

Avoid overwhelming the user.

Use progressive disclosure.

---

# 37. LESSON PAGE UX

Suggested layout:

Left:
curriculum navigation

Center:
lesson content

Right:
context panel

Context panel may include:

* objectives
* prerequisites
* glossary
* bookmarks
* notes
* progress
* related concepts

For long technical lessons provide:

* sticky table of contents
* code blocks
* diagrams
* interactive examples
* checkpoints

---

# 38. EXERCISE UI

Exercise interface should support:

* problem statement
* difficulty
* topic tags
* code editor
* SQL editor
* architecture answer
* text answer
* run tests
* submit
* hints
* attempt history
* solution after completion
* explanations

For coding exercises use a Monaco-style editor if practical.

---

# 39. EXAM MODE UI

Exam mode must remove distractions.

Display:

* exam title
* remaining questions
* progress
* timer if enabled
* flag question
* navigation
* autosave

Do not show:

* hints
* answers
* lesson links

until the exam is submitted.

---

# 40. DESIGN PRINCIPLES

Follow professional UX principles:

* strong visual hierarchy
* low cognitive load
* progressive disclosure
* consistency
* immediate feedback
* clear navigation
* readable typography
* accessible contrast
* keyboard navigation
* responsive layout
* accessibility
* WCAG-minded implementation

Do not add unnecessary visual noise.

Avoid:

* giant gradients
* excessive animations
* meaningless glassmorphism
* decorative dashboards
* random colors
* oversized cards everywhere

Use a mature developer-tool aesthetic similar in spirit to high-quality modern documentation and engineering tools.

---

# 41. DESIGN SYSTEM

Create reusable components and tokens for:

* typography
* spacing
* radius
* shadows
* surfaces
* borders
* semantic colors
* success
* warning
* error
* information
* difficulty levels

Build reusable components such as:

* Button
* Input
* Select
* Dialog
* Sheet
* Tooltip
* Tabs
* Badge
* Progress
* Breadcrumb
* Command palette
* Code block
* Question card
* Exercise card
* Lesson navigation
* Skill meter
* Exam result chart

Support light and dark themes.

---

# 42. FRONTEND ARCHITECTURE

Preferred:

Next.js
TypeScript
React

Use a strong component architecture.

Prefer:

* server/client separation where appropriate
* feature-based organization
* reusable primitives
* accessibility
* good loading states
* proper error states
* skeletons only where useful

Avoid giant components.

Avoid excessive global state.

---

# 43. BACKEND ARCHITECTURE

Use:

Python
FastAPI
PostgreSQL
SQLAlchemy
Alembic

Use a modular monolith initially.

Suggested structure:

app/
modules/
users/
curriculum/
lessons/
exercises/
assessments/
exams/
progress/
projects/
reviews/

Use clear separation between:

* API
* application/services
* domain
* persistence
* infrastructure

But do not overengineer.

---

# 44. DATABASE DESIGN

Design normalized schemas for:

users

tracks

modules

lessons

lesson_dependencies

concepts

exercises

exercise_attempts

exercise_hints

solutions

projects

project_tasks

exams

exam_sections

exam_questions

exam_attempts

exam_answers

skills

skill_mastery

review_items

bookmarks

notes

progress

curriculum_versions

Support versioning of curriculum content.

---

# 45. CONTENT STORAGE

Educational content should not be hard-coded inside React components.

Use a structured content system.

Options:

* Markdown/MDX
* database-backed content
* JSON/YAML metadata + Markdown

Choose a maintainable architecture.

Lessons should support:

* prose
* code
* SQL
* diagrams
* tables
* quizzes
* exercises
* references

---

# 46. SEARCH

Implement global search over:

* lessons
* concepts
* exercises
* projects
* notes

Support keyboard shortcut:

Cmd/Ctrl + K

---

# 47. PERSONAL NOTES

Allow me to write notes against:

* lessons
* concepts
* exercises

Support bookmarks.

---

# 48. CODE QUALITY

Use:

* SOLID where appropriate
* DRY
* KISS
* YAGNI
* clear names
* small cohesive modules
* type safety
* linting
* formatting
* tests

Do not generate huge god classes or giant service files.

---

# 49. TESTING REQUIREMENTS

Add automated tests for critical behavior.

Backend:

* domain logic
* progress
* mastery calculations
* exercise grading
* exam grading
* permissions
* API endpoints

Frontend:

* important components
* exercise flow
* exam flow
* progress UI

Include end-to-end tests for:

* completing lesson
* solving exercise
* submitting exam
* viewing results

---

# 50. SEED CONTENT

Do not create empty curriculum pages.

Populate the project with real initial content.

At minimum create representative complete Modules for:

1. Advanced Python
2. PostgreSQL transactions and locking
3. HTTP idempotency and retries
4. Distributed-system failures
5. Outbox pattern
6. FastAPI architecture
7. Redis and queues
8. Docker production deployment
9. LLM fundamentals
10. Embeddings
11. RAG
12. Tool calling
13. AI evaluation
14. AI security

Every seeded Module should include multiple exercises.

---

# 51. CONTENT QUALITY

Do not generate filler such as:

"Python is a popular programming language."

Content should assume an experienced developer.

Prefer explanations like:

"Python variables are references to objects rather than boxes containing values. This distinction becomes important when reasoning about mutation, aliasing, function arguments, and concurrency."

Use production examples.

---

# 52. QUESTION QUALITY

Avoid trivia like:

"What year was Python created?"

Prefer:

"The following endpoint occasionally creates duplicate orders when the client retries after a timeout. Identify the race and redesign the request flow."

Questions should measure engineering judgment.

---

# 53. ADAPTIVE RECOMMENDATIONS

After exercises or exams, calculate areas needing reinforcement.

Example:

You failed:

* transaction isolation
* Redis locking
* message idempotency

Recommend:

1. Transaction Isolation lesson
2. Locking exercise #7
3. Duplicate-message incident simulation

---

# 54. EXAM READINESS

Calculate readiness for each comprehensive exam.

Example:

Exam 1 readiness: 87%

Weak prerequisites:

* TLS
* Python multiprocessing

Exam 2 readiness: 65%

Weak prerequisites:

* testing
* Docker
* concurrency

Exam 3 readiness: 52%

Weak prerequisites:

* system design
* distributed consistency
* AI evaluation

---

# 55. ENGINEERING DECISION RECORDS

Create an ADR folder.

Document important architectural decisions such as:

* modular monolith vs microservices
* MDX vs database curriculum content
* mastery algorithm
* exam architecture
* exercise grading
* authentication
* caching

Use concise ADRs.

---

# 56. DOCUMENTATION

Create:

README.md

ARCHITECTURE.md

DEVELOPMENT.md

CURRICULUM.md

ASSESSMENT_MODEL.md

DATABASE.md

SECURITY.md

DEPLOYMENT.md

CONTRIBUTING.md

Explain how to add:

* a Track
* a Module
* a Lesson
* an Exercise
* an Exam question
* a Project

---

# 57. DEVELOPMENT EXPERIENCE

Provide:

docker-compose.yml

Makefile or equivalent

.env.example

database migrations

seed scripts

test commands

lint commands

format commands

local development instructions

The project should be easy to start.

Ideal command:

docker compose up

or similarly simple.

---

# 58. SECURITY

Implement:

* password hashing or secure auth provider
* authorization
* validated inputs
* rate-limit-ready design
* secure cookies if used
* CSRF protections where necessary
* safe content rendering
* no leaked secrets
* safe SQL usage
* strong API boundaries

---

# 59. PERFORMANCE

Do not prematurely optimize.

However design for:

* pagination
* indexing
* avoiding N+1 queries
* caching where appropriate
* lazy loading where appropriate
* efficient progress queries

---

# 60. IMPLEMENTATION APPROACH

Work in phases.

Before writing large amounts of code:

PHASE 1

Analyze requirements and produce:

* architecture
* folder structure
* data model
* major domain entities
* UI information architecture
* curriculum structure
* assessment model
* mastery model
* implementation roadmap

Then implement.

PHASE 2

Create foundations:

* project setup
* database
* authentication
* design system
* layout
* curriculum engine

PHASE 3

Implement learning functionality.

PHASE 4

Implement exercises.

PHASE 5

Implement progress/mastery/review.

PHASE 6

Implement exams.

PHASE 7

Populate real curriculum.

PHASE 8

Testing, polish, security, documentation.

Do not stop after scaffolding.

Continue through functional implementation.

---

# 61. IMPORTANT IMPLEMENTATION RULES

Do not:

* create fake buttons
* create dead navigation
* leave TODOs for core functionality
* build only static pages
* build only mock data
* generate meaningless placeholder lessons
* put all logic in frontend components
* create unnecessary microservices
* overuse design patterns
* create duplicated code
* silently ignore errors
* expose exam solutions before completion

Whenever functionality is implemented, make it actually work.

---

# 62. CODE REVIEW YOURSELF

After every major phase, review your own implementation for:

* bugs
* unnecessary complexity
* poor naming
* duplicated logic
* security problems
* missing validation
* race conditions
* poor UX
* accessibility
* performance
* insufficient testing

Fix discovered issues before proceeding.

---

# 63. FINAL ACCEPTANCE CRITERIA

The project is complete when I can:

1. Sign in.
2. See a complete learning path.
3. Open Tracks and Modules.
4. Study real lessons.
5. Solve exercises.
6. Receive hints.
7. Submit solutions.
8. Read explanations.
9. Track mastery.
10. See weak areas.
11. Receive review recommendations.
12. Work on projects.
13. Take Exam 1.
14. Take Exam 2.
15. Take Exam 3.
16. Receive detailed exam analysis.
17. Search the entire curriculum.
18. Bookmark content.
19. Write notes.
20. See exam readiness.
21. Use the application comfortably on desktop and mobile.
22. Run the entire project locally using documented commands.

---

# 64. MOST IMPORTANT PRINCIPLE

The application should teach me to THINK like a senior engineer.

Do not optimize for how much material I have "completed."

Optimize for whether I can:

* understand a problem
* identify constraints
* reason about tradeoffs
* design an appropriate solution
* predict failure modes
* implement safely
* test correctly
* debug production failures
* secure the system
* measure performance
* evaluate AI quality
* explain why my design is correct

A successful graduate of this curriculum should be capable of interviewing for strong Backend Engineer, Backend + AI Engineer, and Applied AI Engineer positions and should possess several production-quality portfolio projects demonstrating those skills.

Start by creating the architecture, curriculum map, data model, UI/UX structure, assessment model, and phased implementation roadmap. Then implement the application systematically until it satisfies the acceptance criteria above.
