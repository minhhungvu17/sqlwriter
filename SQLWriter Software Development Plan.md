# SQLWriter Software Development Plan

### Project Overview

The project has successfully established a foundational pipeline, demonstrating core functionality. These completed items form the basis for the next phase of development:

- **Core Pipeline:** The initial LLM agent pipeline to generate SQL queries from natural language user questions is operational. (AI Task)
- **Tuning & Accuracy:** Question-query retrieval tuning has been completed using prompt engineering techniques derived from CSV data. (AI Task)
- **User Interface (UI):** Basic UI functionality to display the generated SQL query and the resulting database response is implemented. (UI Task)
- **Backend Observability:** Initial logging functionality has been added to the backend for basic tracing and monitoring. (Backend Task)

### Development Plan

| **Priority** | **Category** | **Task Name**                                              | **Owner**  |
| ------------ | ------------ | ---------------------------------------------------------- | ---------- |
| **High**     | Backend      | Session/Chat History API & Schema                          | Backend    |
| **High**     | AI           | Conversational Agent & Task Decomposition & Human-feedback | AI         |
| **High**     | AI           | Agent Router Redesign                                      | AI         |
| **Low**      | Database     | Iceberg Syntax Research & Prompt Update                    | Data/AI    |
| **Low**      | Backend      | Function Calling Execution Engine                          | Backend    |
| **Low**      | UI           | Sidebar History & Human-Intervention UI                    | Frontend   |
| **Low**      | AI           | Integration with local SM LLMs model                       | AI/Backend |

### Phase 1: High Priority (Conversational Core & Architecture)

- That's an excellent and crucial addition. Integrating **Human-in-the-Loop (HITL)** capabilities at key stages is essential for a robust SQL generation tool, especially for debugging and compliance.

  Here is the updated Phase 1 plan, integrating user feedback/intervention points into the core architecture and procedure.

  #### 1. Conversational Agent Design (Backend, System & Human-in-the-Loop)

  **Goal:** Establish the infrastructure for stateful, multi-turn AI interactions, ensuring the system can pause and accept user intervention.

  - **Database Schema:** Design and implement a relational schema to store `Sessions`, `Threads`, and `Messages`. Include a new field within the `Messages` table (e.g., `status: ['pending', 'completed', 'awaiting_human_review']`) to flag where intervention is needed.
  - **Caching Layer:** Implement a caching mechanism (e.g., Redis) to load active conversation context quickly. The cache will store the working state of the agent, including any partially generated SQL or context waiting for user approval.
  - **Context Management:** Develop backend logic for managing the LLM context window. This includes a mechanism to **re-inject human-edited content** (SQL or context) back into the prompt for the next agent step.
  - **AI Agent Router:** Redesign the orchestration flow into a clear Agent Router. This refactor must explicitly include **Human Review Step**.
    - Example: USER_INPUT &rarr; AGENT_ROUTER &rarr; AWAITING_CONTEXT_REVIEW &rarr; COLLECT_CONTEXT_TASK &rarr; GENERATING_SQL &rarr; AWAITING_SQL_REVIEW &rarr; EXECUTING_QUERY &rarr; HUMAN_OR_LLM_FEEDBACK &rarr; LOOP_INTO_AGENT_ROUTER.

  #### 2. Conversational Procedure & Reasoning (AI & Human Intervention)

  **Goal:** Improve query accuracy and enable user correction at critical points in the reasoning process.

  - **Task Decomposition:** Create a prompting strategy that instructs the LLM to break down a complex user question into smaller, logical sub-steps.
    - *HITL Integration:* After decomposition, the system can optionally **pause and display the decomposed steps** to the user for validation ("Are these the right steps to answer your question?").
  - **Keyword & Data Retrieval:** Implement a mechanism to identify keywords and relevant table/column identifiers for each sub-step.
    - *HITL Integration:* Upon successful retrieval, aggregate these findings into a "General Context" block. **Before passing this to the final SQL generation step, the backend must transition to an `AWAITING_CONTEXT_REVIEW` state.**
    - **User Action:** The user must be able to **edit, add, or delete** keywords and schema context directly via the UI.
  - **SQL Generation & Review:**
    - The LLM generates the SQL based on the verified context.
    - *HITL Integration:* **The system must transition to an `AWAITING_SQL_REVIEW` state.** The UI displays the generated query.
    - **User Action:** The user must be able to **edit the generated SQL query** directly. The agent only proceeds to execution once the user confirms the query is correct (e.g., by clicking an "Execute/Approve" button).

### Phase 2: Low Priority (Integration & User Experience)

#### **3. Iceberg Database Integration (Database & AI)**

- **Goal:** Migrate support to the new Iceberg Data Lake architecture.
- **Syntax & Schema Analysis:** Compare the current database syntax with the specific SQL dialect used by the Iceberg engine (e.g., Trino, SparkSQL, Snowflake). Map out schema changes.
- **Prompt Tuning:** Update the System Prompts to strictly enforce the new Iceberg-compatible syntax.
- **Pipeline Verification:** Re-run the existing "CSV prompt tuning" validation set against the new Iceberg syntax to ensure the AI generates valid code for the new environment.

#### **4. Function Calling & Observability (Backend)**

- **Goal:** Enable the AI to take actions and improve system transparency.
- **Task Generation for Function Calls:** Define standard JSON schemas for necessary tools (e.g., `get_table_schema`, `execute_sample_query`, `validate_sql`).
- **Step-by-Step Logging:** Implement granular logging at the backend level. Logs should capture the input, the AI's internal thought process, the specific function called, and the output returned at every step to facilitate debugging.

#### **5. UI Upgrades (Frontend)**

- **Goal:** Provide better information density and user control.
- **Side Panel & History:** Develop a side panel to track conversation history and manage active sessions.
- **Status Tracking:** Implement visual indicators that display the current agent state (e.g., "Analyzing Request," "Retrieving Keywords," "Generating SQL") so the user understands the delay.
- **User Intervention:** Add interface controls that allow the user to pause, edit the generated SQL, or provide feedback/correction at specific steps before the final execution.