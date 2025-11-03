# Design Document

## Overview

This design document outlines the modernization of the Event Planning Agent system using CrewAI as the base framework, LangGraph for workflow orchestration, and MCP servers for enhanced capabilities. The system transforms the existing multi-agent event planning architecture into a more robust, scalable, and maintainable solution while preserving all core business logic and algorithms.

The modernized system maintains the sophisticated beam search optimization, collaborative multi-agent workflow, and vendor scoring algorithms while adding enhanced observability, better error handling, and improved deployment capabilities.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "CrewAI Framework"
        subgraph "Agent Layer"
            OA[Orchestrator Agent]
            BA[Budgeting Agent]
            SA[Sourcing Agent]
            TA[Timeline Agent]
            BLA[Blueprint Agent]
        end
        
        subgraph "LangGraph Workflow Engine"
            WS[Workflow State]
            BS[Beam Search Controller]
            SC[State Controller]
        end
        
        subgraph "MCP Server Layer"
            VDS[Vendor Data Server]
            CS[Calculation Server]
            MS[Monitoring Server]
        end
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL)]
        ES[Event State Store]
    end
    
    subgraph "External Interfaces"
        API[REST API]
        WH[Webhooks]
    end
    
    API --> OA
    OA --> WS
    WS --> BS
    BS --> BA
    BS --> SA
    BS --> TA
    SA --> VDS
    BA --> CS
    OA --> BLA
    WS --> PG
    MS --> WH
```

### Component Architecture

The system is built on three foundational layers:

1. **CrewAI Agent Framework**: Manages agent lifecycle, communication, and coordination
2. **LangGraph Workflow Engine**: Handles complex state management and iterative processes
3. **MCP Server Integration**: Provides specialized tools and external service integration

## Components and Interfaces

### 1. CrewAI Agent Layer

#### Orchestrator Agent (CrewAI Agent)
- **Role**: Master coordinator and workflow manager
- **Responsibilities**:
  - Initialize planning sessions
  - Manage beam search algorithm (k=3)
  - Coordinate inter-agent communication
  - Handle client interactions
  - Persist workflow state

```python
class OrchestratorAgent(Agent):
    role = "Event Planning Coordinator"
    goal = "Find optimal event combinations through collaborative agent workflow"
    backstory = "Expert event planner with deep knowledge of vendor optimization"
    tools = [BeamSearchTool, StateManagementTool, ClientCommunicationTool]
```

#### Budgeting Agent (CrewAI Agent)
- **Role**: Financial controller and optimization specialist
- **Responsibilities**:
  - Generate budget allocations using Gemma-2B LLM
  - Calculate fitness scores for event combinations
  - Manage cost constraints and optimization

```python
class BudgetingAgent(Agent):
    role = "Financial Optimization Specialist"
    goal = "Optimize budget allocation and calculate combination fitness scores"
    backstory = "Financial expert specializing in event budget optimization"
    tools = [BudgetAllocationTool, FitnessCalculationTool]
    llm = Ollama(model="gemma:2b")
```
#### Sourcing Agent (CrewAI Agent)
- **Role**: Vendor procurement and qualification specialist
- **Responsibilities**:
  - Parse client requirements using TinyLLaMA
  - Execute parameterized SQL queries
  - Rank vendors using weighted linear scoring

```python
class SourcingAgent(Agent):
    role = "Vendor Sourcing Specialist"
    goal = "Find and rank optimal vendors based on client requirements"
    backstory = "Procurement expert with deep vendor network knowledge"
    tools = [HybridFilterTool, VendorDatabaseTool, VendorRankingTool]
    llm = Ollama(model="tinyllama")
```

#### Timeline Agent (CrewAI Agent)
- **Role**: Logistics and feasibility specialist
- **Responsibilities**:
  - Perform conflict detection algorithms
  - Validate vendor compatibility
  - Generate detailed event timelines

```python
class TimelineAgent(Agent):
    role = "Event Logistics Coordinator"
    goal = "Ensure logistical feasibility and create detailed timelines"
    backstory = "Operations expert specializing in event logistics"
    tools = [ConflictDetectionTool, TimelineGenerationTool]
    llm = Ollama(model="gemma:2b")
```

#### Blueprint Agent (CrewAI Agent)
- **Role**: Final document generation specialist
- **Responsibilities**:
  - Compile final event blueprints
  - Generate professional documentation
  - Format client deliverables

```python
class BlueprintAgent(Agent):
    role = "Event Documentation Specialist"
    goal = "Create comprehensive event blueprints and documentation"
    backstory = "Documentation expert with event planning expertise"
    tools = [BlueprintGenerationTool, DocumentFormattingTool]
    llm = Ollama(model="gemma:2b")
```

### 2. LangGraph Workflow Engine

#### Workflow State Management
```python
class EventPlanningState(TypedDict):
    client_request: dict
    budget_allocations: List[dict]
    vendor_combinations: List[dict]
    beam_candidates: List[dict]
    selected_combination: Optional[dict]
    final_blueprint: Optional[str]
    workflow_status: str
    iteration_count: int
```

#### Beam Search Implementation
```python
def beam_search_node(state: EventPlanningState) -> EventPlanningState:
    """LangGraph node implementing beam search algorithm"""
    current_beam = state["beam_candidates"]
    new_combinations = generate_combinations(state)
    
    # Score all combinations
    scored_combinations = []
    for combo in new_combinations:
        score = calculate_fitness_score(combo, state["client_request"])
        scored_combinations.append((combo, score))
    
    # Keep top k=3 combinations
    top_combinations = sorted(scored_combinations, key=lambda x: x[1], reverse=True)[:3]
    
    return {
        **state,
        "beam_candidates": [combo for combo, score in top_combinations],
        "iteration_count": state["iteration_count"] + 1
    }
```

#### Workflow Graph Definition
```python
workflow = StateGraph(EventPlanningState)

# Add nodes
workflow.add_node("initialize", initialize_planning)
workflow.add_node("budget_allocation", budget_allocation_node)
workflow.add_node("vendor_sourcing", vendor_sourcing_node)
workflow.add_node("beam_search", beam_search_node)
workflow.add_node("client_selection", client_selection_node)
workflow.add_node("blueprint_generation", blueprint_generation_node)

# Add edges
workflow.add_edge(START, "initialize")
workflow.add_edge("initialize", "budget_allocation")
workflow.add_edge("budget_allocation", "vendor_sourcing")
workflow.add_edge("vendor_sourcing", "beam_search")
workflow.add_conditional_edges(
    "beam_search",
    should_continue_search,
    {
        "continue": "vendor_sourcing",
        "present_options": "client_selection"
    }
)
workflow.add_edge("client_selection", "blueprint_generation")
workflow.add_edge("blueprint_generation", END)
```

### 3. MCP Server Integration

#### Vendor Data MCP Server
```python
class VendorDataServer:
    """MCP server for enhanced vendor data processing"""
    
    @mcp_tool
    def enhanced_vendor_search(self, filters: dict, preferences: dict) -> List[dict]:
        """Enhanced vendor search with ML-based ranking"""
        pass
    
    @mcp_tool
    def vendor_compatibility_check(self, vendors: List[dict]) -> dict:
        """Check compatibility between selected vendors"""
        pass
    
    @mcp_tool
    def vendor_availability_check(self, vendor_id: str, date: str) -> bool:
        """Real-time vendor availability checking"""
        pass
```

#### Calculation MCP Server
```python
class CalculationServer:
    """MCP server for complex calculations and optimizations"""
    
    @mcp_tool
    def fitness_score_calculation(self, combination: dict, preferences: dict) -> float:
        """Enhanced fitness score calculation with ML features"""
        pass
    
    @mcp_tool
    def budget_optimization(self, total_budget: float, requirements: dict) -> List[dict]:
        """Advanced budget allocation optimization"""
        pass
    
    @mcp_tool
    def cost_prediction(self, vendors: List[dict], guest_count: int) -> dict:
        """Predict total costs with confidence intervals"""
        pass
```

#### Monitoring MCP Server
```python
class MonitoringServer:
    """MCP server for system monitoring and observability"""
    
    @mcp_tool
    def log_agent_interaction(self, agent_name: str, action: str, data: dict):
        """Log agent interactions for monitoring"""
        pass
    
    @mcp_tool
    def track_workflow_performance(self, workflow_id: str, metrics: dict):
        """Track workflow performance metrics"""
        pass
    
    @mcp_tool
    def generate_health_report(self) -> dict:
        """Generate system health report"""
        pass
```

## Data Models

### Enhanced Database Schema

The existing PostgreSQL schema is preserved with additional tables for workflow management:

```sql
-- Enhanced event_plans table with LangGraph state
CREATE TABLE event_plans (
    plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    plan_data JSONB,
    workflow_state JSONB,  -- New: LangGraph state
    beam_history JSONB,    -- New: Beam search history
    agent_logs JSONB,      -- New: Agent interaction logs
    final_blueprint TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- New: Agent performance tracking
CREATE TABLE agent_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES event_plans(plan_id),
    agent_name VARCHAR(100),
    task_name VARCHAR(100),
    execution_time_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- New: Workflow metrics
CREATE TABLE workflow_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES event_plans(plan_id),
    total_iterations INTEGER,
    total_execution_time_ms INTEGER,
    combinations_evaluated INTEGER,
    final_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### CrewAI Task Definitions

```python
# Budget allocation task
budget_task = Task(
    description="Generate 3 budget allocation strategies for {total_budget} budget",
    expected_output="JSON with 3 budget allocation options",
    agent=budgeting_agent,
    tools=[BudgetAllocationTool]
)

# Vendor sourcing task
sourcing_task = Task(
    description="Source and rank vendors for {service_type} within {budget} budget",
    expected_output="Ranked list of top 5 vendors with scores",
    agent=sourcing_agent,
    tools=[HybridFilterTool, VendorDatabaseTool],
    context=[budget_task]
)

# Combination evaluation task
evaluation_task = Task(
    description="Evaluate vendor combinations and calculate fitness scores",
    expected_output="Scored combinations with detailed analysis",
    agent=budgeting_agent,
    tools=[FitnessCalculationTool],
    context=[sourcing_task]
)
```

## Error Handling

### Multi-Layer Error Handling Strategy

1. **Agent Level**: Each CrewAI agent handles tool-specific errors
2. **Workflow Level**: LangGraph manages state recovery and retry logic
3. **MCP Level**: MCP servers provide graceful degradation
4. **System Level**: Global error handlers and monitoring

```python
class ErrorHandlingMiddleware:
    """Comprehensive error handling for the event planning system"""
    
    def handle_agent_error(self, agent_name: str, error: Exception, context: dict):
        """Handle agent-specific errors with recovery strategies"""
        if isinstance(error, DatabaseConnectionError):
            return self.retry_with_backoff(agent_name, context)
        elif isinstance(error, LLMTimeoutError):
            return self.fallback_to_deterministic_logic(context)
        else:
            return self.escalate_error(agent_name, error, context)
    
    def handle_workflow_error(self, state: EventPlanningState, error: Exception):
        """Handle workflow-level errors with state recovery"""
        # Save current state
        self.save_recovery_checkpoint(state)
        
        # Attempt recovery based on error type
        if isinstance(error, BeamSearchError):
            return self.recover_beam_search(state)
        else:
            return self.restart_from_checkpoint(state)
```

## Testing Strategy

### Multi-Level Testing Approach

1. **Unit Tests**: Individual agent and tool testing
2. **Integration Tests**: Agent collaboration testing
3. **Workflow Tests**: End-to-end LangGraph workflow testing
4. **Performance Tests**: Load and stress testing
5. **MCP Tests**: MCP server functionality testing

```python
class EventPlanningSystemTests:
    """Comprehensive test suite for the modernized system"""
    
    def test_agent_collaboration(self):
        """Test CrewAI agent collaboration"""
        crew = Crew(
            agents=[orchestrator_agent, budgeting_agent, sourcing_agent],
            tasks=[budget_task, sourcing_task],
            verbose=True
        )
        result = crew.kickoff(inputs=test_client_data)
        assert result.success
    
    def test_langgraph_workflow(self):
        """Test LangGraph workflow execution"""
        app = workflow.compile()
        result = app.invoke(initial_state)
        assert result["workflow_status"] == "completed"
    
    def test_mcp_integration(self):
        """Test MCP server integration"""
        vendor_server = VendorDataServer()
        result = vendor_server.enhanced_vendor_search(test_filters, test_preferences)
        assert len(result) > 0
```## Imple
mentation Architecture

### Project Structure
```
event_planning_agent_v2/
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py
│   ├── budgeting.py
│   ├── sourcing.py
│   ├── timeline.py
│   └── blueprint.py
├── workflows/
│   ├── __init__.py
│   ├── planning_workflow.py
│   └── state_models.py
├── tools/
│   ├── __init__.py
│   ├── budget_tools.py
│   ├── vendor_tools.py
│   ├── timeline_tools.py
│   └── blueprint_tools.py
├── mcp_servers/
│   ├── __init__.py
│   ├── vendor_server.py
│   ├── calculation_server.py
│   └── monitoring_server.py
├── database/
│   ├── __init__.py
│   ├── models.py
│   ├── migrations.py
│   └── setup.py
├── api/
│   ├── __init__.py
│   ├── routes.py
│   ├── middleware.py
│   └── schemas.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── mcp_config.json
├── tests/
│   ├── unit/
│   ├── integration/
│   └── performance/
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── mcp-servers.yml
├── requirements.txt
├── pyproject.toml
└── README.md
```

### Technology Stack Integration

#### Core Framework Stack
- **CrewAI**: Agent framework and orchestration
- **LangGraph**: Workflow state management and execution
- **FastAPI**: REST API framework
- **PostgreSQL**: Primary database with JSONB support
- **Ollama**: Local LLM inference (Gemma-2B, TinyLLaMA)

#### MCP Integration Stack
- **MCP Protocol**: Model Context Protocol for tool integration
- **uvx**: MCP server execution environment
- **Custom MCP Servers**: Specialized calculation and monitoring tools

#### Monitoring and Observability
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboards
- **Structured Logging**: JSON-based logging with correlation IDs

### Migration Strategy

#### Phase 1: Foundation Setup
1. Set up CrewAI agent framework
2. Implement basic LangGraph workflow
3. Migrate existing database schema
4. Create MCP server infrastructure

#### Phase 2: Agent Migration
1. Convert existing tools to CrewAI agents
2. Implement workflow state management
3. Add error handling and recovery
4. Integrate MCP servers

#### Phase 3: Enhancement and Optimization
1. Add advanced monitoring and observability
2. Implement performance optimizations
3. Add new MCP-powered features
4. Complete testing and documentation

### Configuration Management

#### Environment Configuration
```python
# config/settings.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str
    
    # LLM Configuration
    ollama_base_url: str = "http://localhost:11434"
    gemma_model: str = "gemma:2b"
    tinyllama_model: str = "tinyllama"
    
    # CrewAI Configuration
    crew_verbose: bool = True
    max_iterations: int = 10
    
    # LangGraph Configuration
    beam_width: int = 3
    max_workflow_iterations: int = 20
    
    # MCP Configuration
    mcp_servers_config: str = "config/mcp_config.json"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
```

#### MCP Server Configuration
```json
{
  "mcpServers": {
    "vendor-data-server": {
      "command": "uvx",
      "args": ["event-planning-vendor-server@latest"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}",
        "LOG_LEVEL": "INFO"
      },
      "disabled": false,
      "autoApprove": ["enhanced_vendor_search", "vendor_compatibility_check"]
    },
    "calculation-server": {
      "command": "uvx", 
      "args": ["event-planning-calculation-server@latest"],
      "env": {
        "LOG_LEVEL": "INFO"
      },
      "disabled": false,
      "autoApprove": ["fitness_score_calculation", "budget_optimization"]
    },
    "monitoring-server": {
      "command": "uvx",
      "args": ["event-planning-monitoring-server@latest"],
      "env": {
        "PROMETHEUS_URL": "${PROMETHEUS_URL}",
        "LOG_LEVEL": "INFO"
      },
      "disabled": false,
      "autoApprove": ["log_agent_interaction", "track_workflow_performance"]
    }
  }
}
```

### Deployment Architecture

#### Docker Composition
```yaml
# docker-compose.yml
version: '3.8'
services:
  event-planning-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/eventdb
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - postgres
      - ollama
      - mcp-servers
  
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: eventdb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  ollama:
    image: ollama/ollama
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
  
  mcp-servers:
    build: ./docker/mcp-servers
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/eventdb
    depends_on:
      - postgres

volumes:
  postgres_data:
  ollama_data:
```

### Performance Considerations

#### Optimization Strategies
1. **Database Optimization**:
   - Proper indexing on frequently queried columns
   - Connection pooling for concurrent requests
   - Query optimization for vendor searches

2. **LLM Optimization**:
   - Model caching and warm-up
   - Batch processing for multiple requests
   - Fallback to deterministic logic when needed

3. **Workflow Optimization**:
   - Parallel agent execution where possible
   - State checkpointing for long-running workflows
   - Intelligent beam search pruning

4. **MCP Server Optimization**:
   - Connection pooling and reuse
   - Caching of frequently requested data
   - Asynchronous processing for non-critical operations

### Security Considerations

#### Multi-Layer Security
1. **API Security**:
   - JWT-based authentication
   - Rate limiting and request validation
   - CORS configuration

2. **Database Security**:
   - Connection encryption
   - Parameterized queries (SQL injection prevention)
   - Role-based access control

3. **MCP Security**:
   - Server authentication and authorization
   - Secure communication channels
   - Input validation and sanitization

4. **Infrastructure Security**:
   - Container security scanning
   - Network segmentation
   - Secrets management

This design provides a comprehensive modernization path that preserves all existing functionality while adding significant improvements in maintainability, observability, and scalability through the integration of CrewAI, LangGraph, and MCP servers.