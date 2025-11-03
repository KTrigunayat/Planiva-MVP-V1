# Event Planning Agent v2 - Complete System Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture & Components](#architecture--components)
3. [File Structure Analysis](#file-structure-analysis)
4. [Core Agents](#core-agents)
5. [Tools & Utilities](#tools--utilities)
6. [Database Layer](#database-layer)
7. [API Layer](#api-layer)
8. [Workflow Engine](#workflow-engine)
9. [Streamlit GUI](#streamlit-gui)
10. [Configuration & Settings](#configuration--settings)
11. [Testing & Validation](#testing--validation)
12. [Deployment & Operations](#deployment--operations)
13. [Complete Workflow Explanation](#complete-workflow-explanation)

---

## System Overview

The Event Planning Agent v2 is a sophisticated AI-powered event planning system that leverages multiple specialized agents working in coordination to create optimal event plans. The system is built using modern AI frameworks including CrewAI for multi-agent orchestration, LangGraph for workflow management, and integrates with local LLM models through Ollama.

### Key Features

- **Multi-Agent AI System**: Five specialized agents (Orchestrator, Budgeting, Sourcing, Timeline, Blueprint)
- **Beam Search Optimization**: Advanced k=3 beam search algorithm for optimal vendor combinations
- **Real-time Progress Tracking**: Live updates during planning process
- **Comprehensive Database**: PostgreSQL with vendor data and state management
- **Modern API**: FastAPI with async support and comprehensive documentation
- **Interactive GUI**: Streamlit-based user interface for client interaction
- **MCP Integration**: Model Context Protocol servers for enhanced capabilities

### Technology Stack

- **AI Frameworks**: CrewAI, LangGraph, LangChain
- **LLM Models**: Ollama (Gemma-2B, TinyLLaMA)
- **Database**: PostgreSQL with JSONB support
- **API**: FastAPI with Pydantic schemas
- **Frontend**: Streamlit
- **Containerization**: Docker & Docker Compose
- **Monitoring**: Prometheus, Grafana
- **Testing**: Pytest with comprehensive test suites

---

## Architecture & Components

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI       │    │   PostgreSQL    │
│   Frontend      │◄──►│   Backend       │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   LangGraph     │
                    │   Workflow      │
                    │   Engine        │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   CrewAI        │
                    │   Multi-Agent   │
                    │   System        │
                    └─────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
            ┌─────────────┐    ┌─────────────┐
            │   Ollama    │    │   MCP       │
            │   LLMs      │    │   Servers   │
            └─────────────┘    └─────────────┘
```

### Component Interaction Flow

1. **Client Input**: User submits event requirements through Streamlit GUI
2. **API Processing**: FastAPI receives and validates the request
3. **Workflow Orchestration**: LangGraph manages the multi-step workflow
4. **Agent Coordination**: CrewAI coordinates specialized agents
5. **LLM Processing**: Ollama provides AI capabilities for decision making
6. **Data Management**: PostgreSQL stores state and vendor information
7. **Result Delivery**: Optimized event plans returned to client

---

## File Structure Analysis

### Root Directory Structure

```
event_planning_agent_v2/
├── agents/                 # CrewAI agent implementations
├── api/                   # FastAPI application and routes
├── config/                # Configuration management
├── database/              # Database models and management
├── docker/                # Docker configuration files
├── docs/                  # Documentation
├── error_handling/        # Error handling and recovery
├── llm/                   # LLM management utilities
├── logs/                  # Application logs
├── mcp_servers/           # MCP server implementations
├── monitoring/            # Monitoring and observability
├── observability/         # Logging and metrics
├── scripts/               # Deployment and utility scripts
├── tests/                 # Test suites
├── tools/                 # CrewAI tools
├── workflows/             # LangGraph workflow definitions
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
└── pyproject.toml        # Project configuration
```

### Key Configuration Files

#### `main.py` - Application Entry Point
- **Purpose**: Main FastAPI application initialization
- **Functions**: 
  - `main()`: Entry point for uvicorn server
  - Health check endpoints
  - CORS and middleware configuration
- **Dependencies**: FastAPI, uvicorn, custom middleware

#### `requirements.txt` - Dependencies
- **Core AI**: crewai, langgraph, langchain, ollama
- **Web Framework**: fastapi, uvicorn, pydantic
- **Database**: psycopg2-binary, sqlalchemy, alembic
- **Monitoring**: prometheus-client, structlog
- **Testing**: pytest, pytest-asyncio, pytest-cov

#### `pyproject.toml` - Project Configuration
- **Build System**: setuptools configuration
- **Dependencies**: Core and optional dependencies
- **Scripts**: CLI entry points
- **Tool Configuration**: black, mypy, pytest settings

---

## Core Agents

### 1. Orchestrator Agent (`agents/orchestrator.py`)

**Purpose**: Master coordinator managing the entire workflow and beam search optimization.

**Key Functions**:
- `create_orchestrator_agent()`: Creates the orchestrator with Gemma-2B LLM
- `create_orchestrator_tasks()`: Defines coordination tasks
- Beam search coordination with k=3 optimization
- Client communication management
- Workflow state management

**Tools Used**:
- `BeamSearchTool`: Implements beam search algorithm with fitness scoring
- `StateManagementTool`: Manages LangGraph workflow state persistence
- `ClientCommunicationTool`: Handles client interactions and updates

**LLM Model**: Gemma-2B for coordination and decision making

**Key Responsibilities**:
- Initialize planning workflow
- Coordinate beam search optimization (k=3)
- Present options to client for selection
- Manage workflow state transitions
- Handle client communication

### 2. Budgeting Agent (`agents/budgeting.py`)

**Purpose**: Financial optimization specialist handling budget allocation and fitness scoring.

**Key Functions**:
- `create_budgeting_agent()`: Creates budgeting agent with Gemma-2B
- `create_budget_allocation_task()`: Generates budget allocation strategies
- `create_fitness_calculation_task()`: Evaluates vendor combinations
- `BudgetingAgentCoordinator`: Manages budgeting workflows

**Tools Used**:
- `BudgetAllocationTool`: Generates multiple budget allocation strategies
- `FitnessCalculationTool`: Calculates comprehensive fitness scores

**LLM Model**: Gemma-2B for financial analysis and optimization

**Key Responsibilities**:
- Generate 3 budget allocation strategies (luxury, standard, intimate)
- Calculate fitness scores for vendor combinations
- Optimize budget allocation based on vendor feedback
- Provide cost variance analysis

### 3. Sourcing Agent (`agents/sourcing.py`)

**Purpose**: Vendor procurement specialist using advanced filtering and ranking.

**Key Functions**:
- `create_sourcing_agent()`: Creates sourcing agent with TinyLLaMA
- `create_vendor_sourcing_task()`: Sources vendors for specific services
- `create_multi_service_sourcing_task()`: Coordinates multi-service sourcing
- `SourcingAgentCoordinator`: Manages sourcing workflows

**Tools Used**:
- `HybridFilterTool`: Processes client requirements into filters
- `VendorDatabaseTool`: Queries PostgreSQL with advanced filtering
- `VendorRankingTool`: Generates LLM-based vendor summaries

**LLM Model**: TinyLLaMA for requirement parsing and vendor analysis

**Key Responsibilities**:
- Parse complex client requirements
- Execute sophisticated database queries
- Rank vendors using weighted linear scoring
- Generate vendor summaries and recommendations

### 4. Timeline Agent (`agents/timeline.py`)

**Purpose**: Logistics coordinator ensuring feasibility and creating detailed timelines.

**Key Functions**:
- `create_timeline_agent()`: Creates timeline agent with Gemma-2B
- `create_conflict_detection_task()`: Detects vendor and timeline conflicts
- `create_timeline_generation_task()`: Creates detailed event schedules
- `TimelineAgentCoordinator`: Manages timeline workflows

**Tools Used**:
- `ConflictDetectionTool`: Analyzes vendor availability and conflicts
- `TimelineGenerationTool`: Generates comprehensive event timelines

**LLM Model**: Gemma-2B for timeline planning and optimization

**Key Responsibilities**:
- Detect potential conflicts between vendors
- Create detailed event timelines with coordination points
- Validate timeline feasibility
- Optimize vendor coordination strategies

### 5. Blueprint Agent (`agents/blueprint.py`)

**Purpose**: Documentation specialist creating comprehensive event blueprints.

**Key Functions**:
- `create_blueprint_agent()`: Creates blueprint agent with Gemma-2B
- `create_blueprint_generation_task()`: Generates complete event documentation
- `create_document_formatting_task()`: Formats documents professionally
- `BlueprintAgentCoordinator`: Manages blueprint workflows

**Tools Used**:
- `BlueprintGenerationTool`: Compiles comprehensive event blueprints
- `DocumentFormattingTool`: Formats documents in multiple formats

**LLM Model**: Gemma-2B for document generation and formatting

**Key Responsibilities**:
- Generate comprehensive event blueprints
- Create professional documentation
- Format documents in multiple formats (PDF, HTML, Markdown)
- Perform quality assurance on generated documents

---

## Tools & Utilities

### Vendor Tools (`tools/vendor_tools.py`)

#### `HybridFilterTool`
- **Purpose**: Processes client requirements into hard filters and soft preferences
- **Input**: Client data dictionary and service type
- **Output**: Structured filter object with hard/soft preferences
- **Key Methods**:
  - `_extract_hard_filters()`: Deterministic filter extraction
  - `_extract_soft_preferences_with_llm()`: LLM-based preference analysis

#### `VendorDatabaseTool`
- **Purpose**: Queries PostgreSQL database with advanced filtering and ranking
- **Input**: Filter JSON string with service type and preferences
- **Output**: Top 5 ranked vendors with scores
- **Key Methods**:
  - `_get_db_connection()`: Database connection management
  - `_calculate_preference_score()`: Weighted preference scoring
- **Scoring Weights**: Configurable per service type (price vs. preference)

#### `VendorRankingTool`
- **Purpose**: Generates LLM-based vendor summaries
- **Input**: Vendor list and client vision
- **Output**: Batch vendor summaries
- **LLM Integration**: Uses Gemma-2B for contextual summaries

### Budget Tools (`tools/budget_tools.py`)

#### `BudgetAllocationTool`
- **Purpose**: Generates multiple budget allocation strategies
- **Input**: Total budget, client requirements, service types
- **Output**: 3 allocation strategies with fitness scores
- **Allocation Templates**:
  - **Luxury**: Venue 45%, Catering 35%, Photography 12%, Makeup 8%
  - **Standard**: Venue 40%, Catering 40%, Photography 15%, Makeup 5%
  - **Intimate**: Venue 35%, Catering 45%, Photography 15%, Makeup 5%

#### `FitnessCalculationTool`
- **Purpose**: Calculates comprehensive fitness scores for vendor combinations
- **Input**: Vendor combination, client requirements, budget allocation
- **Output**: Detailed fitness analysis with component breakdown
- **Scoring Components**:
  - **Budget Fitness** (40%): Budget compliance and cost optimization
  - **Preference Fitness** (45%): Client preference matching
  - **Compatibility Fitness** (15%): Vendor coordination feasibility

### Timeline Tools (`tools/timeline_tools.py`)

#### `ConflictDetectionTool`
- **Purpose**: Detects conflicts in vendor combinations and timelines
- **Input**: Vendor combination, event date, proposed timeline
- **Output**: Conflict analysis with feasibility score
- **Conflict Types**: Availability, timeline overlap, location conflicts

#### `TimelineGenerationTool`
- **Purpose**: Creates detailed event timelines with vendor coordination
- **Input**: Client requirements, vendor combination, event details
- **Output**: Comprehensive timeline with coordination points
- **Features**: Setup requirements, vendor assignments, critical milestones

### Blueprint Tools (`tools/blueprint_tools.py`)

#### `BlueprintGenerationTool`
- **Purpose**: Compiles comprehensive event blueprints
- **Input**: Client requirements, vendor combination, timeline, budget
- **Output**: Complete event blueprint document
- **Sections**: Executive summary, vendor profiles, timeline, budget breakdown

#### `DocumentFormattingTool`
- **Purpose**: Formats blueprints in multiple formats
- **Input**: Blueprint content, format type, client branding
- **Output**: Professionally formatted document
- **Formats**: Markdown, HTML, PDF (with reportlab integration)

---

## Database Layer

### Models (`database/models.py`)

#### Vendor Models
- **`Venue`**: Venue information with capacity, location, pricing
- **`Caterer`**: Catering services with cuisine types, pricing
- **`Photographer`**: Photography services with packages, availability
- **`MakeupArtist`**: Makeup services with pricing, location

#### Workflow Models
- **`EventPlan`**: Enhanced with LangGraph state management
  - `workflow_state`: Current LangGraph state (JSONB)
  - `beam_history`: Beam search iteration history
  - `agent_logs`: Agent interaction logs
  - `final_blueprint`: Generated event blueprint

#### Monitoring Models
- **`AgentPerformance`**: Individual agent task execution metrics
- **`WorkflowMetrics`**: End-to-end workflow performance
- **`SystemHealth`**: Component health monitoring

### Database Setup (`database/setup.py`)

#### `initialize_database()`
- Creates all database tables
- Tests connectivity
- Sets up indexes for performance

#### Key Features
- **JSONB Support**: Flexible data storage for complex objects
- **UUID Primary Keys**: Distributed system compatibility
- **Performance Indexes**: Optimized queries for vendor search
- **State Management**: LangGraph workflow state persistence

### Connection Management (`database/connection.py`)

#### Features
- **Sync/Async Sessions**: Support for both synchronous and asynchronous operations
- **Connection Pooling**: Efficient database connection management
- **Error Handling**: Robust error handling and recovery
- **Health Checks**: Database connectivity monitoring

---

## API Layer

### Routes (`api/routes.py`)

#### Core Endpoints

##### `POST /v1/plans` - Create Event Plan
- **Input**: `EventPlanRequest` with client requirements
- **Output**: `EventPlanResponse` with plan ID and status
- **Features**: 
  - Synchronous and asynchronous execution modes
  - Background task processing
  - Real-time status updates

##### `GET /v1/plans/{plan_id}` - Get Plan Status
- **Input**: Plan ID
- **Output**: Complete plan information with workflow status
- **Features**:
  - Detailed workflow status reporting
  - Agent performance metrics
  - Real-time progress updates

##### `POST /v1/plans/{plan_id}/select-combination` - Select Combination
- **Input**: `CombinationSelection` with combination ID
- **Output**: Updated plan with selected combination
- **Features**:
  - Automatic blueprint generation
  - Client feedback integration
  - Background processing

##### `GET /v1/plans` - List Plans
- **Input**: Pagination and filter parameters
- **Output**: `PlanListResponse` with filtered plans
- **Features**:
  - Pagination support
  - Status and client name filtering
  - Comprehensive plan summaries

#### Background Tasks
- **`_execute_workflow_background()`**: Asynchronous workflow execution
- **`_resume_workflow_background()`**: Workflow resumption
- **`_generate_blueprint_background()`**: Blueprint generation

### Schemas (`api/schemas.py`)

#### Request/Response Models
- **`EventPlanRequest`**: Client event planning request
- **`EventPlanResponse`**: Complete event plan information
- **`CombinationSelection`**: Vendor combination selection
- **`WorkflowStatus`**: Real-time workflow execution status

#### Data Models
- **`VendorInfo`**: Vendor information structure
- **`EventCombination`**: Vendor combination with scoring
- **`GuestCount`**: Flexible guest count handling
- **Preference Models**: Structured preference definitions

---

## Workflow Engine

### LangGraph Workflow (`workflows/planning_workflow.py`)

#### `EventPlanningWorkflowNodes`
Main workflow orchestrator implementing beam search with k=3 optimization.

##### Key Nodes

###### `initialize_planning()`
- Validates client request
- Initializes workflow metadata
- Sets up state management
- **Output**: Initialized workflow state

###### `budget_allocation_node()`
- Executes Budgeting Agent tasks
- Generates 3 budget allocation strategies
- Calculates fitness scores
- **Output**: Budget allocations with scores

###### `vendor_sourcing_node()`
- Executes Sourcing Agent tasks
- Sources vendors for each budget allocation
- Creates vendor combinations
- **Output**: Vendor combinations for evaluation

###### `beam_search_node()`
- **Core Algorithm**: Implements optimized beam search with k=3
- Evaluates all vendor combinations
- Maintains top 3 candidates (beam width)
- **Optimization Features**:
  - Early termination for high-quality solutions
  - Convergence detection
  - Memory optimization
  - Performance caching

###### `client_selection_node()`
- Prepares combinations for client presentation
- Formats vendor information
- Manages client selection process
- **Output**: Client-ready combination options

#### State Models (`workflows/state_models.py`)

##### `EventPlanningState` (TypedDict)
LangGraph-compatible state definition with comprehensive workflow tracking.

**Core Fields**:
- `plan_id`: Unique plan identifier
- `client_request`: Original client requirements
- `workflow_status`: Current workflow status
- `iteration_count`: Beam search iteration counter
- `budget_allocations`: Generated budget strategies
- `vendor_combinations`: Sourced vendor combinations
- `beam_candidates`: Top k=3 combinations
- `selected_combination`: Final client selection
- `final_blueprint`: Generated event blueprint

##### Validation Models
- **`EventPlanningStateValidator`**: Pydantic validation for state integrity
- **`StateTransitionLogger`**: Comprehensive state transition tracking
- **`WorkflowMetadata`**: Workflow execution metadata

#### Execution Engine (`workflows/execution_engine.py`)

##### `ExecutionEngine`
Manages workflow execution with monitoring and error handling.

**Features**:
- **Execution Modes**: Synchronous and asynchronous execution
- **Checkpointing**: State persistence at key points
- **Error Recovery**: Automatic retry and recovery mechanisms
- **Performance Monitoring**: Detailed execution metrics
- **Resource Management**: Memory and CPU optimization

---

## Streamlit GUI

The Streamlit GUI provides an intuitive interface for clients to interact with the Event Planning Agent v2 system.

### Core Components

#### Forms (`components/forms.py`)

##### `EventPlanningForm`
Comprehensive multi-section form for event planning requirements.

**Sections**:
1. **Basic Information**: Client details, event type, date, location
2. **Guest Information**: Guest counts for different event segments
3. **Budget & Priorities**: Total budget and allocation preferences
4. **Venue Preferences**: Venue types, amenities, location preferences
5. **Catering Preferences**: Cuisine types, dietary requirements, service style
6. **Photography & Services**: Photography style, videography, additional services
7. **Client Vision & Theme**: Detailed vision, themes, color schemes

**Features**:
- **Progressive Navigation**: Step-by-step form completion
- **Real-time Validation**: Immediate feedback on form inputs
- **Data Persistence**: Session state management
- **Progress Tracking**: Visual progress indicators

#### Progress Tracking (`components/progress.py`)

##### `ProgressTracker`
Real-time workflow progress monitoring and visualization.

**Features**:
- **Live Updates**: Real-time progress percentage and status
- **Agent Activity**: Current agent and task information
- **Step Completion**: Visual indicators for completed steps
- **Error Handling**: Error display and recovery options
- **Time Estimation**: Estimated completion times

#### Results Display (`components/results.py`)

##### `ResultsManager`
Comprehensive vendor combination display and comparison tools.

**Features**:
- **Combination Cards**: Visual vendor combination summaries
- **Detailed Views**: Comprehensive vendor information
- **Comparison Tools**: Side-by-side combination analysis
- **Filtering & Sorting**: Advanced result filtering options
- **Selection Interface**: Easy combination selection

#### Blueprint Display (`components/blueprint.py`)

##### `BlueprintManager`
Professional blueprint presentation and export capabilities.

**Features**:
- **Comprehensive Display**: Complete event plan visualization
- **Timeline Integration**: Interactive timeline display
- **Vendor Directory**: Complete vendor contact information
- **Export Options**: Multiple format downloads (PDF, JSON, HTML)
- **Email Sharing**: Direct email integration

### Page Structure

#### `pages/plan_status.py` - Progress Monitoring
- Real-time workflow status
- Agent activity monitoring
- Error handling and recovery
- Performance metrics display

#### `pages/plan_results.py` - Results Review
- Vendor combination display
- Comparison and filtering tools
- Selection interface
- Detailed vendor information

#### `pages/plan_blueprint.py` - Final Blueprint
- Comprehensive event plan display
- Timeline and logistics
- Export and sharing options
- Implementation guidance

---

## Configuration & Settings

### Settings Management (`config/settings.py`)

#### `Settings` Class
Comprehensive configuration management using Pydantic settings.

**Configuration Categories**:
- **Database**: Connection strings, pool settings
- **API**: Host, port, CORS settings
- **LLM**: Ollama configuration, model settings
- **Workflow**: Beam width, iteration limits, optimization settings
- **Monitoring**: Logging levels, metrics configuration

#### Environment Configuration
- **Development**: `.env.development` with debug settings
- **Production**: `.env.production` with optimized settings
- **Testing**: `.env.test` with test-specific configuration

### MCP Configuration (`config/mcp_config.json`)

#### MCP Server Definitions
- **Vendor Data Server**: Enhanced vendor search capabilities
- **Calculation Server**: Advanced optimization algorithms
- **Monitoring Server**: System health and performance monitoring

**Configuration Features**:
- **Auto-approval**: Automatic tool approval for trusted operations
- **Environment-specific**: Different configurations per environment
- **Security**: Secure server communication settings

---

## Testing & Validation

### Test Structure

#### Unit Tests (`tests/unit/`)
- **`test_agents.py`**: Individual agent functionality
- **`test_tools.py`**: Tool validation and performance
- **`test_mcp_servers.py`**: MCP server integration

#### Integration Tests (`tests/integration/`)
- **`test_agent_collaboration.py`**: Multi-agent coordination
- **`test_langgraph_workflow.py`**: Workflow execution
- **`test_performance_algorithms.py`**: Algorithm performance

#### System Tests (`tests/`)
- **`test_api_endpoints.py`**: API functionality
- **`test_end_to_end_validation.py`**: Complete workflow testing
- **`test_system_health.py`**: System monitoring and health

### Validation Tools

#### `test_simple_validation.py`
Basic system validation for quick health checks.

#### `run_api_system_tests.py`
Comprehensive API testing suite with performance benchmarks.

#### Performance Testing
- **Load Testing**: High-volume request handling
- **Stress Testing**: System limits and recovery
- **Algorithm Performance**: Beam search optimization validation

---

## Deployment & Operations

### Docker Configuration (`docker/`)

#### `docker-compose.yml`
Complete system deployment with all components.

**Services**:
- **API Server**: FastAPI application
- **Database**: PostgreSQL with extensions
- **Ollama**: Local LLM inference
- **Monitoring**: Prometheus and Grafana
- **MCP Servers**: Enhanced capability servers

#### `Dockerfile`
Optimized container image with:
- Multi-stage builds for size optimization
- Security best practices
- Performance optimizations
- Health check integration

### Deployment Scripts (`scripts/`)

#### `deploy-prod.sh`
Production deployment automation with:
- Environment validation
- Database migrations
- Service health checks
- Rollback capabilities

#### `deploy-dev.sh`
Development environment setup with:
- Local development configuration
- Debug mode enablement
- Hot reload capabilities

### Monitoring (`monitoring/`)

#### Prometheus Configuration
- **Metrics Collection**: Application and system metrics
- **Alert Rules**: Automated alerting for issues
- **Performance Monitoring**: Response times and throughput

#### Grafana Dashboards
- **System Overview**: High-level system health
- **Agent Performance**: Individual agent metrics
- **Workflow Analytics**: End-to-end workflow performance
- **Database Monitoring**: Database performance and health

---

## Complete Workflow Explanation

### Overview
When a client submits event planning requirements, the system orchestrates a complex multi-agent workflow that leverages AI capabilities, database queries, and optimization algorithms to generate optimal event plans.

### Detailed Step-by-Step Process

#### Phase 1: Request Initialization (0-5%)

1. **Client Input Processing**
   - Client submits requirements through Streamlit GUI
   - Form validation ensures all required fields are present
   - Data is structured into standardized format
   - Plan ID is generated and initial database record created

2. **API Request Handling**
   - FastAPI receives the structured request
   - Request validation using Pydantic schemas
   - Background task initialization for async processing
   - Initial response sent to client with plan ID

3. **Workflow Initialization**
   - LangGraph workflow state is created
   - Initial state includes client requirements and metadata
   - Workflow status set to "initialized"
   - State persistence in PostgreSQL database

#### Phase 2: Budget Allocation (5-25%)

4. **Budgeting Agent Activation**
   - Orchestrator Agent delegates to Budgeting Agent
   - Client requirements analyzed for event type determination
   - Guest count and vision keywords processed

5. **Event Type Classification**
   ```python
   # Event type determination logic
   guest_count = max(client_requirements.get('guestCount', {}).values())
   vision = client_requirements.get('clientVision', '').lower()
   
   if guest_count > 500 or 'luxury' in vision:
       event_type = "luxury"
   elif guest_count < 200 or 'intimate' in vision:
       event_type = "intimate"
   else:
       event_type = "standard"
   ```

6. **Budget Strategy Generation**
   - Three allocation strategies generated based on event type:
     - **Strategy 1**: Balanced allocation using base template
     - **Strategy 2**: Venue-focused (10% increase to venue budget)
     - **Strategy 3**: Experience-focused (increased photography/makeup)

7. **Fitness Score Calculation**
   - Each strategy evaluated using preserved calculateFitnessScore algorithm
   - Scoring considers client priorities and guest count
   - Strategies ranked by fitness score

#### Phase 3: Vendor Sourcing (25-60%)

8. **Sourcing Agent Activation**
   - For each budget allocation strategy, Sourcing Agent activated
   - TinyLLaMA model used for requirement parsing

9. **Requirement Processing**
   - **Hard Filters Extraction** (Deterministic):
     ```python
     # Example hard filters for venue
     hard_filters = {
         'location_city': extracted_from_vision,
         'capacity_min': max_guest_count,
         'required_amenities': essential_amenities,
         'venue_type': venue_preferences
     }
     ```
   
   - **Soft Preferences Extraction** (LLM-based):
     ```python
     # LLM prompt for soft preferences
     prompt = f"""
     Analyze client vision: "{client_vision}"
     Extract style preferences as JSON:
     {{"style": ["keywords"], "atmosphere": ["descriptors"]}}
     """
     ```

10. **Database Query Execution**
    - PostgreSQL queries with parameterized filters
    - Optimized queries using performance indexes
    - Results limited by budget constraints

11. **Vendor Ranking Algorithm**
    - **Weighted Linear Scoring Model**:
      ```python
      # Service-specific weights
      weights = {
          'venue': {'price': 0.7, 'preference': 0.3},
          'caterer': {'price': 0.6, 'preference': 0.4},
          'photographer': {'price': 0.4, 'preference': 0.6},
          'makeup_artist': {'price': 0.5, 'preference': 0.5}
      }
      
      # Final score calculation
      ranking_score = (weights['price'] * price_score) + 
                     (weights['preference'] * preference_score)
      ```

12. **Vendor Summary Generation**
    - Gemma-2B LLM generates contextual summaries
    - Batch processing for efficiency
    - Client vision integration for relevance

#### Phase 4: Beam Search Optimization (60-80%)

13. **Beam Search Algorithm Execution**
    - **Core Algorithm**: Preserved k=3 beam search optimization
    - All vendor combinations evaluated and scored
    - Top 3 combinations maintained (beam width = 3)

14. **Fitness Score Calculation for Combinations**
    ```python
    # Comprehensive fitness scoring
    def calculate_fitness_score(combination, client_requirements):
        # Budget compliance (40% weight)
        budget_score = evaluate_budget_compliance(combination)
        
        # Preference matching (45% weight)  
        preference_score = evaluate_preference_matching(combination)
        
        # Vendor compatibility (15% weight)
        compatibility_score = evaluate_vendor_compatibility(combination)
        
        return (0.4 * budget_score + 
                0.45 * preference_score + 
                0.15 * compatibility_score)
    ```

15. **Iterative Optimization**
    - Multiple iterations of vendor sourcing and beam search
    - Convergence detection for early termination
    - Performance optimization with caching

16. **Termination Conditions**
    - Maximum iterations reached (default: 20)
    - Convergence detected (score differences < threshold)
    - High-quality solution found (score > 0.8)

#### Phase 5: Timeline & Conflict Analysis (80-90%)

17. **Timeline Agent Activation**
    - Detailed event timeline generation
    - Vendor coordination point identification

18. **Conflict Detection**
    - **Availability Conflicts**: Vendor calendar checking
    - **Timeline Overlaps**: Activity scheduling conflicts
    - **Location Conflicts**: Geographic coordination challenges
    - **Service Constraints**: Vendor-specific limitations

19. **Feasibility Assessment**
    ```python
    # Feasibility scoring algorithm
    def calculate_feasibility_score(vendor_combination, timeline):
        conflicts = detect_conflicts(vendor_combination, timeline)
        
        # Scoring based on conflict severity
        high_severity_penalty = len(conflicts['high']) * 0.3
        medium_severity_penalty = len(conflicts['medium']) * 0.1
        low_severity_penalty = len(conflicts['low']) * 0.05
        
        feasibility_score = 1.0 - (high_severity_penalty + 
                                  medium_severity_penalty + 
                                  low_severity_penalty)
        
        return max(0.0, feasibility_score)
    ```

#### Phase 6: Client Presentation (90-95%)

20. **Option Preparation**
    - Top 3 combinations formatted for client presentation
    - Detailed vendor information compilation
    - Cost breakdowns and highlights generation

21. **Client Communication**
    - Professional presentation format
    - Clear selection instructions
    - Vendor contact information
    - Implementation recommendations

#### Phase 7: Blueprint Generation (95-100%)

22. **Blueprint Agent Activation** (Upon client selection)
    - Comprehensive event blueprint compilation
    - Professional document formatting

23. **Blueprint Components**
    - **Executive Summary**: Event overview and highlights
    - **Vendor Partner Profiles**: Detailed vendor information
    - **Event Timeline**: Hour-by-hour schedule with coordination
    - **Budget Breakdown**: Detailed cost analysis
    - **Implementation Guide**: Next steps and recommendations
    - **Contact Directory**: Complete vendor contact information

24. **Quality Assurance**
    - Completeness validation against client requirements
    - Data accuracy verification
    - Professional presentation assessment
    - Final approval for client delivery

25. **Multi-Format Export**
    - **PDF**: Professional print-ready document
    - **HTML**: Web-optimized interactive version
    - **JSON**: Machine-readable data format
    - **Markdown**: Plain text structured format

### Behind-the-Scenes Technical Details

#### State Management
- **LangGraph State**: Comprehensive workflow state tracking
- **Database Persistence**: PostgreSQL with JSONB for complex objects
- **Checkpointing**: Regular state snapshots for recovery
- **Transaction Management**: ACID compliance for data integrity

#### Performance Optimizations
- **Caching**: Vendor query results and fitness score caching
- **Connection Pooling**: Efficient database connection management
- **Async Processing**: Non-blocking operations for scalability
- **Memory Management**: Optimized data structures and cleanup

#### Error Handling & Recovery
- **Graceful Degradation**: Fallback mechanisms for component failures
- **Retry Logic**: Automatic retry for transient failures
- **Error Logging**: Comprehensive error tracking and analysis
- **Recovery Procedures**: Workflow resumption from checkpoints

#### Monitoring & Observability
- **Real-time Metrics**: Performance and health monitoring
- **Structured Logging**: Detailed execution tracing
- **Alert Systems**: Automated issue detection and notification
- **Performance Analytics**: Continuous system optimization

### Integration Points

#### External Systems
- **Ollama LLM Server**: Local AI model inference
- **PostgreSQL Database**: Vendor data and state management
- **MCP Servers**: Enhanced capability integration
- **Monitoring Stack**: Prometheus and Grafana integration

#### API Integrations
- **RESTful API**: Standard HTTP/JSON communication
- **WebSocket Support**: Real-time updates (future enhancement)
- **Webhook Integration**: Event-driven notifications
- **Authentication**: Secure API access (configurable)

This comprehensive workflow ensures that every client receives an optimized, feasible, and professionally documented event plan that meets their specific requirements while staying within budget constraints. The system's multi-agent architecture, combined with advanced AI capabilities and robust engineering practices, delivers consistent, high-quality results at scale.

---

*This documentation provides a complete technical overview of the Event Planning Agent v2 system. For specific implementation details, refer to the individual source files and their inline documentation.*