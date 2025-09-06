AI Podcast Generation EngineA scalable, event-driven pipeline for automatically generating podcast episodes from a brief using AI.System ArchitectureThe system uses a hybrid orchestration model to combine the resilience of an event-driven architecture with the observability of a workflow management tool.Kafka: Acts as the event-driven backbone for task queuing and service decoupling. Each stage of the pipeline is triggered by a message on a dedicated Kafka topic.Prefect: Provides a high-level orchestration layer for observability, automatic retries, logging, and centralized failure handling. The Prefect flow definition shadows the event-driven pipeline.MongoDB: Serves as the persistence layer for job state and artifact metadata. It is the single source of truth, allowing the Kafka and Prefect systems to coordinate state indirectly via a repository pattern.S3: Object storage for large binary artifacts, primarily the generated audio files.Job Lifecycle Diagram1. POST /api/v1/podcast/create
      |
      v
2. Supervisor Agent
      |--> Creates Job Document in MongoDB
      |--> Produces message to 'outline_generation' Kafka Topic
      |--> Triggers Prefect 'podcast_generation_flow'
      |
      v
3. Kafka Workers & Prefect Flow (run in parallel)
      |
      |   [Kafka Worker] consumes message -> calls [Agent]
      |   [Prefect Task] runs              -> calls [Agent]
      |
      v
4. Agent (e.g., OutlineAgent, TTSAgent)
      |--> Executes business logic (e.g., AI calls)
      |--> Updates MongoDB document and/or uploads artifact to S3
      |--> Produces message to the next Kafka topic for the subsequent stage
      |
      ... repeats until the final 'publish' step ...
Key Componentsapi/: FastAPI service for job ingestion via a REST API.agents/: Contains the core business logic for each pipeline stage (e.g., OutlineAgent, TTSAgent). Agents are the single source of truth for performing work.workers/: Kafka consumers that listen on specific topics and trigger the corresponding agent's process method.orchestration/flows/: Defines the Prefect flow (podcast_generation_flow.py) that mirrors the pipeline for monitoring and management.database/: Implements the Repository Pattern (PodcastRepository) to abstract all MongoDB interactions.messaging/: Reusable Kafka client for producing and consuming messages.Local Setup and Usage1. PrerequisitesDockerDocker Compose2. Environment SetupCopy the example environment file and populate it with the necessary credentials and configuration.cp .env.example .env
# Edit .env with your credentials (S3, OpenAI, etc.)
3. Run the SystemBuild and run all services using Docker Compose.docker-compose up --build
4. Deploy the Prefect FlowOnce the containers are running, execute the deployment script inside the prefect-worker container.docker-compose exec prefect-worker python scripts/deploy_prefect_simple.py
5. Accessing ServicesAPI (Swagger UI): http://localhost:5050/docsPrefect UI: http://localhost:42006. Interacting with the APICreate a JobSubmit a job via the API. The response will contain the job_id.curl -X POST http://localhost:5050/api/v1/podcast/create \
   -H "Content-Type: application/json" \
   -d '{
     "topic": "The History of Artificial Intelligence",
     "tone": "informative and engaging",
     "length_minutes": 10,
     "target_audience": "tech enthusiasts",
     "user_email": "test@example.com"
   }'
Check Job StatusCheck the status of a running job using its job_id.curl -X GET http://localhost:5050/api/v1/podcast/your_job_id_here/status
