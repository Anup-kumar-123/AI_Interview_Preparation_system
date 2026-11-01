"""
Question bank for the Guided Interview.

Each role has 12 questions ordered from fundamentals to advanced. The level decides
which window of the list is used, and the questions are then sampled at random, so
every new interview is different. Gemini generates fresh questions when available;
this bank is the offline fallback and the top-up source.
"""
import random

IT_ROLES = [
    "Machine Learning Engineer",
    "AI Engineer (LLM / GenAI)",
    "Data Scientist",
    "Data Engineer",
    "Data Analyst",
    "Software Development Engineer (SDE)",
    "Frontend Developer",
    "Full Stack Developer",
    "DevOps Engineer",
    "Cloud Engineer",
    "Cybersecurity Analyst",
    "QA / Test Automation Engineer",
    "Mobile App Developer",
    "System Architect",
]

# 0-2 years = Entry, 3-6 = Mid, 7-10 = High
def level_from_years(years: int) -> str:
    years = int(years)
    if years <= 2:
        return "Entry"
    if years <= 6:
        return "Mid"
    return "High"


# (start, end) slice of the easy->hard list used for each level
LEVEL_WINDOW = {"Entry": (0, 9), "Mid": (2, 11), "High": (3, 12)}

ROLE_TOPICS = {
    "Machine Learning Engineer": ["model evaluation", "feature engineering", "overfitting", "MLOps and deployment", "data drift", "model optimisation"],
    "AI Engineer (LLM / GenAI)": ["prompt design", "RAG pipelines", "hallucination control", "LLM evaluation", "AI agents and tools", "cost and latency"],
    "Data Scientist": ["statistics", "A/B testing", "forecasting", "model interpretation", "business problem framing", "causal inference"],
    "Data Engineer": ["ETL and ELT", "data modelling", "streaming pipelines", "data quality", "query optimisation", "data lake design"],
    "Data Analyst": ["SQL joins and windows", "data cleaning", "dashboards", "KPIs", "metric investigation", "stakeholder communication"],
    "Software Development Engineer (SDE)": ["data structures", "algorithms", "OOP and design", "API design", "debugging", "concurrency"],
    "Frontend Developer": ["JavaScript fundamentals", "React state", "accessibility", "web performance", "browser rendering", "frontend security"],
    "Full Stack Developer": ["request lifecycle", "authentication", "database choice", "API design", "caching", "deployment"],
    "DevOps Engineer": ["CI/CD", "containers", "Kubernetes", "infrastructure as code", "monitoring", "incident response"],
    "Cloud Engineer": ["IAM and security", "networking and VPC", "auto-scaling", "cost optimisation", "migration", "disaster recovery"],
    "Cybersecurity Analyst": ["web attacks", "incident response", "SIEM and alerting", "encryption", "vulnerability management", "zero trust"],
    "QA / Test Automation Engineer": ["test strategy", "automation frameworks", "API testing", "flaky tests", "performance testing", "CI integration"],
    "Mobile App Developer": ["app lifecycle", "state management", "offline support", "app performance", "mobile security", "release management"],
    "System Architect": ["scalability", "consistency and CAP", "caching", "event-driven design", "high availability", "technical trade-offs"],
}

ROLE_QUESTIONS = {
    "Machine Learning Engineer": [
        "Explain the difference between overfitting and underfitting and how you detect each.",
        "How do you choose evaluation metrics for an imbalanced classification problem?",
        "Walk me through your process for cleaning data and engineering features for a new model.",
        "Explain the bias-variance trade-off with a practical example.",
        "How would you choose between a linear model, a tree-based model and a neural network for a tabular problem?",
        "How do you prevent data leakage when building training and validation sets?",
        "Describe how you would deploy a model as an API and monitor it in production.",
        "How do you detect and handle data drift and concept drift after deployment?",
        "How would you speed up training or inference for a model that is too slow or too large?",
        "How would you design an ML pipeline that is reproducible, versioned and testable?",
        "How would you design a real-time recommendation system serving millions of users?",
        "How do you decide when an ML solution is not worth building, and how do you guide a team through that decision?",
    ],
    "AI Engineer (LLM / GenAI)": [
        "What is the difference between a traditional ML model and a large language model?",
        "Explain what a prompt, a system prompt and temperature are, and how each affects output.",
        "What is retrieval-augmented generation and when would you use it instead of fine-tuning?",
        "How do you chunk documents and choose an embedding model for a RAG system?",
        "How do you reduce hallucinations in an LLM-powered application?",
        "How would you evaluate the quality of an LLM application beyond manual spot checks?",
        "Describe how you would build an agent that calls external tools safely.",
        "How do you manage latency, cost and rate limits for a production LLM feature?",
        "When would you fine-tune a model, and how would you prepare and validate the training data?",
        "How do you defend an LLM application against prompt injection and data leakage?",
        "Design a multi-tenant AI assistant over private company data. What are the key components and risks?",
        "How do you set up evaluation, guardrails and rollback when model versions keep changing?",
    ],
    "Data Scientist": [
        "Explain the difference between supervised and unsupervised learning with examples.",
        "How do you handle missing values and outliers, and when does each approach fail?",
        "Explain p-values and confidence intervals to a non-technical stakeholder.",
        "How would you design and analyse an A/B test, including sample size and duration?",
        "Walk me through how you approach a business problem from question to model.",
        "How do you choose between precision, recall and F1 for a business use case?",
        "How would you explain a model's predictions to a skeptical stakeholder?",
        "Describe a time you found that the data could not answer the question that was asked.",
        "How would you build a forecasting model for a seasonal business metric?",
        "How do you check that a claimed uplift is causal and not just correlation?",
        "How do you prioritise data science projects by expected business impact?",
        "How would you set standards for experimentation and model review across a data science team?",
    ],
    "Data Engineer": [
        "What is the difference between ETL and ELT, and when would you choose each?",
        "Explain normalisation and when denormalisation is the better choice.",
        "How do you design a table schema for analytics versus transactions?",
        "How would you make a data pipeline idempotent and safe to re-run?",
        "Explain batch versus streaming processing with a use case for each.",
        "How do you monitor data quality and handle bad records in a pipeline?",
        "How would you optimise a slow SQL query or Spark job over a very large table?",
        "How would you partition and store data in a data lake for fast queries?",
        "How do you handle schema changes from upstream sources without breaking consumers?",
        "Design a pipeline that ingests millions of events per minute with exactly-once guarantees.",
        "How would you design data lineage, access control and cost governance for a company's data platform?",
        "How do you decide between building a custom pipeline and buying a managed tool?",
    ],
    "Data Analyst": [
        "What is the difference between a primary key and a foreign key, and why do they matter in joins?",
        "Explain the different types of SQL joins with an example of each.",
        "How do you clean a messy dataset before analysis?",
        "How do you choose the right chart to show a trend versus a comparison?",
        "What KPIs would you track for an e-commerce product, and why?",
        "How do you validate that a dashboard shows correct numbers?",
        "How would you investigate a sudden drop in a key metric?",
        "How would you use window functions to solve a ranking or running-total problem?",
        "Tell me how you turned an analysis into a decision for non-technical stakeholders.",
        "How do you handle conflicting definitions of a metric across teams?",
        "How would you design a self-service reporting layer for a growing company?",
        "How do you prioritise analysis requests when everything is marked urgent?",
    ],
    "Software Development Engineer (SDE)": [
        "Explain the difference between a process and a thread.",
        "What is the time and space complexity of common operations on arrays, hash maps and trees?",
        "Explain object-oriented principles such as encapsulation and polymorphism with an example.",
        "How do you write code that is easy to test and maintain?",
        "How would you debug a bug that only happens in production?",
        "Explain how a hash map works internally and what happens on collisions.",
        "How do you design a REST API that is versioned, secure and easy to use?",
        "How do you find and fix performance bottlenecks in production code?",
        "Explain database indexing and the trade-offs of adding indexes.",
        "Design a URL shortener that handles heavy read traffic. What are the trade-offs?",
        "How do you handle concurrency problems such as race conditions and deadlocks?",
        "How do you lead a technical decision when the team disagrees on the approach?",
    ],
    "Frontend Developer": [
        "Explain the difference between var, let and const in JavaScript.",
        "What is the CSS box model, and how do flexbox and grid differ?",
        "Explain how the browser renders a page from HTML to pixels.",
        "How do you make a web page responsive and accessible?",
        "Explain how state is managed in a component-based framework such as React.",
        "What causes unnecessary re-renders and how do you prevent them?",
        "How do you improve Core Web Vitals such as loading speed and layout shift?",
        "How do you handle API errors, loading states and caching in the UI?",
        "Explain cross-site scripting and how a frontend developer protects against it.",
        "How would you structure a large frontend codebase and its shared design system?",
        "How would you design a micro-frontend or monorepo setup for several teams?",
        "How do you set up testing and performance budgets for a large user-facing app?",
    ],
    "Full Stack Developer": [
        "Explain how a request travels from the browser to the database and back.",
        "What is the difference between SQL and NoSQL databases, and how do you choose?",
        "How do authentication and authorization differ, and how do you implement them?",
        "Explain REST versus GraphQL and when you would choose each.",
        "How do you structure a project so the frontend and backend can evolve independently?",
        "How do you handle file uploads and long-running tasks in a web application?",
        "How would you cache data at the browser, API and database layers?",
        "How would you set up CI/CD for a full stack application?",
        "How do you protect an application against attacks such as SQL injection and CSRF?",
        "Design a real-time chat feature. Which technologies and trade-offs would you pick?",
        "How would you scale a monolith that is slowing down as traffic grows?",
        "How do you decide when to split a full stack app into separate services?",
    ],
    "DevOps Engineer": [
        "What is CI/CD and why does it matter?",
        "Explain the difference between a container and a virtual machine.",
        "What are the key parts of a Dockerfile and how do you keep images small and safe?",
        "Explain Infrastructure as Code and the benefit of tools like Terraform.",
        "How do you design a deployment pipeline with automated tests and rollbacks?",
        "Explain Kubernetes pods, deployments and services.",
        "How do you set up monitoring, logging and alerting for a service?",
        "How do you handle secrets and configuration across environments?",
        "How would you run a blameless post-mortem after an outage?",
        "How would you implement blue-green or canary deployments?",
        "How would you design a multi-region, highly available platform and its disaster recovery plan?",
        "How do you balance reliability targets (SLOs) with the pace of releases?",
    ],
    "Cloud Engineer": [
        "What are IaaS, PaaS and SaaS, with an example of each?",
        "Explain regions and availability zones and why they matter.",
        "How do you secure access with IAM roles and least privilege?",
        "How would you design a VPC with public and private subnets?",
        "Explain object, block and file storage and when to use each.",
        "How do you set up auto-scaling and load balancing for a web application?",
        "How do you monitor and reduce cloud costs?",
        "How would you migrate an on-premise application to the cloud?",
        "Compare serverless functions and containers for a new workload.",
        "How do you design backup, disaster recovery and data residency compliance?",
        "Design a secure multi-account cloud landing zone for a large company.",
        "How do you decide between a single-cloud and a multi-cloud strategy?",
    ],
    "Cybersecurity Analyst": [
        "Explain the CIA triad with examples.",
        "What is the difference between symmetric and asymmetric encryption?",
        "Explain common web attacks such as SQL injection, XSS and CSRF.",
        "What happens when you type a URL into a browser, from a security point of view?",
        "How do you triage and respond to a phishing report?",
        "What is a SIEM and how do you tune alerts to reduce false positives?",
        "Explain the stages of an incident response process.",
        "How do you perform a vulnerability assessment and prioritise the findings?",
        "How would you investigate a suspected compromised account?",
        "Explain zero trust and how you would apply it to a company network.",
        "How would you build a threat-detection programme mapped to MITRE ATT&CK?",
        "How do you communicate risk and justify security spending to leadership?",
    ],
    "QA / Test Automation Engineer": [
        "What is the difference between verification and validation?",
        "Explain the testing pyramid and what belongs at each level.",
        "How do you write a good bug report?",
        "How do you decide which test cases to automate first?",
        "Explain the difference between smoke, sanity and regression testing.",
        "How do you test an API, including negative and edge cases?",
        "How do you keep automated UI tests stable and not flaky?",
        "How would you design a test strategy for a new feature with a tight deadline?",
        "How would you test performance and load for a web service?",
        "How do you integrate automated tests into a CI pipeline?",
        "How would you build a test automation framework from scratch for a growing team?",
        "How do you measure and improve overall product quality, beyond counting bugs?",
    ],
    "Mobile App Developer": [
        "Explain the Android or iOS app lifecycle.",
        "What is the difference between native and cross-platform development?",
        "How do you store data locally and keep it in sync with a server?",
        "How do you handle different screen sizes and device capabilities?",
        "How do you manage state in a mobile app?",
        "How do you handle poor or missing network connectivity?",
        "How do you reduce app size, startup time and battery use?",
        "How do you secure data and API keys in a mobile app?",
        "How do you handle push notifications and background work?",
        "Describe your release process, including staged rollouts and crash monitoring.",
        "How would you architect a large app built by several teams?",
        "How do you decide between one cross-platform codebase and separate native apps?",
    ],
    "System Architect": [
        "What is the difference between monolithic and microservice architectures?",
        "Explain the CAP theorem with a practical example.",
        "How do you choose between SQL and NoSQL for a new system?",
        "Explain horizontal versus vertical scaling.",
        "How do you make a system highly available and fault tolerant?",
        "What caching strategies do you know, and what are the invalidation risks?",
        "How would you design an API gateway and service-to-service communication?",
        "Explain event-driven architecture and when message queues help.",
        "Design a ride-sharing platform. Which components and data stores would you pick?",
        "How do you handle data consistency across several services?",
        "How do you document architecture decisions and evolve a legacy system safely?",
        "How do you balance technical debt, cost and delivery speed when setting architecture direction?",
    ],
}

BEHAVIORAL = [
    "Tell me about yourself and why you chose a career in IT.",
    "Describe a time you had to learn a new technology quickly.",
    "Tell me about a time you made a mistake at work. What did you do?",
    "Describe a disagreement with a teammate and how you resolved it.",
    "Tell me about a time you worked under a tight deadline.",
    "How do you keep your technical skills up to date?",
    "Describe a time you received critical feedback and how you responded.",
    "Tell me about a time you helped a teammate who was stuck.",
    "Describe a situation where requirements changed suddenly. How did you adapt?",
    "Tell me about the technical achievement you are proudest of.",
    "Describe a time you had to make a decision with incomplete information.",
    "Where do you see your career in the next three years?",
]

PROJECT_TEMPLATES = [
    "In {project}, what problem were you solving and what exactly was your own contribution?",
    "Why did you choose {tech} for {project}, and what alternatives did you consider?",
    "What was the hardest technical challenge in {project} and how did you solve it?",
    "How did you test and validate that {project} worked correctly?",
    "What measurable result or impact did {project} deliver?",
    "If you rebuilt {project} today, what would you change and why?",
    "How did you work with others on {project}, and how did you handle blockers or disagreements?",
    "How would you scale {project} to 100 times the load, and where would it break first?",
    "What bugs or mistakes did you run into on {project}, and what did you learn from them?",
    "How did you deploy and monitor {project}?",
]


def offline_role_questions(role, level, count=10, behavioral=3, avoid=None, rng=None):
    """Random, level-appropriate questions. Prefers questions not seen earlier in this session."""
    rng = rng or random.Random()
    avoid = {q.lower() for q in (avoid or [])}
    pool = ROLE_QUESTIONS.get(role) or ROLE_QUESTIONS[IT_ROLES[0]]
    lo, hi = LEVEL_WINDOW.get(level, LEVEL_WINDOW["Mid"])
    window = pool[lo:hi]

    def pick(source, n):
        fresh = [q for q in source if q.lower() not in avoid]
        stale = [q for q in source if q.lower() in avoid]
        rng.shuffle(fresh)
        rng.shuffle(stale)
        return (fresh + stale)[:n]

    questions = pick(window, count - behavioral) + pick(BEHAVIORAL, behavioral)
    rng.shuffle(questions)
    return questions


def offline_project_questions(projects, count, rng=None):
    """Template questions spread across the candidate's projects."""
    rng = rng or random.Random()
    if not projects:
        return []
    order = {i: rng.sample(PROJECT_TEMPLATES, len(PROJECT_TEMPLATES)) for i in range(len(projects))}
    out = []
    for n in range(count):
        i = n % len(projects)
        template = order[i][(n // len(projects)) % len(PROJECT_TEMPLATES)]
        p = projects[i]
        out.append({
            "project": p["name"],
            "question": template.format(project=p["name"], tech=(p.get("tech") or "that technology stack")),
        })
    return out
