# Event Planning Workflow with Task Management Integration

## Complete Workflow Diagram

```mermaid
graph TD
    START([START]) --> initialize[Initialize Planning]
    
    initialize --> budget[Budget Allocation]
    budget --> sourcing[Vendor Sourcing]
    sourcing --> beam[Beam Search]
    
    beam -->|continue| sourcing
    beam -->|present_options| client[Client Selection]
    
    client -->|wait_selection| END1([END - Wait for Selection])
    client -->|selection_made| task_mgmt[Task Management]
    
    task_mgmt -->|timeline_data present| process[Process Extended Tasks]
    task_mgmt -->|timeline_data missing| skip[Skip Processing]
    
    process --> blueprint[Blueprint Generation]
    skip --> blueprint
    
    blueprint --> END2([END - Complete])
    
    style task_mgmt fill:#90EE90,stroke:#006400,stroke-width:3px
    style process fill:#90EE90,stroke:#006400,stroke-width:2px
    style skip fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px
```

## Task Management Node Detail

```mermaid
graph TD
    A[Task Management Node Entry] --> B{Timeline Data<br/>Available?}
    
    B -->|No| C[Log Warning]
    C --> D[Skip Processing]
    D --> E[Set next_node = blueprint_generation]
    E --> Z[Return State]
    
    B -->|Yes| F[Instantiate TaskManagementAgent]
    F --> G[Call process_with_error_handling]
    
    G --> H{Processing<br/>Successful?}
    
    H -->|Yes| I[Update extended_task_list]
    I --> J[Log Success]
    J --> K[Save State]
    K --> L[Set next_node = blueprint_generation]
    L --> Z
    
    H -->|No| M[Log Error]
    M --> N[Update error_count]
    N --> O[Set last_error]
    O --> P[Set next_node = blueprint_generation]
    P --> Z
    
    style A fill:#4169E1,stroke:#000080,stroke-width:2px,color:#fff
    style F fill:#90EE90,stroke:#006400,stroke-width:2px
    style G fill:#90EE90,stroke:#006400,stroke-width:2px
    style I fill:#90EE90,stroke:#006400,stroke-width:2px
    style D fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px
    style M fill:#FFB6C1,stroke:#DC143C,stroke-width:2px
    style Z fill:#4169E1,stroke:#000080,stroke-width:2px,color:#fff
```

## State Flow Through Task Management

```mermaid
sequenceDiagram
    participant WF as Workflow
    participant TM as Task Management Node
    participant AG as TaskManagementAgent
    participant SM as StateManager
    participant TL as TransitionLogger
    
    WF->>TM: EventPlanningState
    TM->>TL: log_node_entry()
    
    alt Timeline Data Present
        TM->>AG: Instantiate Agent
        TM->>AG: process_with_error_handling(state)
        AG->>AG: Process Sub-Agents
        AG->>AG: Process Tools
        AG->>AG: Generate Extended Task List
        AG-->>TM: Updated State with extended_task_list
        TM->>SM: save_workflow_state()
        TM->>TL: log_node_exit(success=True)
    else Timeline Data Missing
        TM->>TL: log_node_exit(status=skipped)
    end
    
    TM-->>WF: Updated State (next_node=blueprint_generation)
```

## Integration Points

### Input Dependencies
- **timeline_data**: Required for task management processing
- **selected_combination**: Vendor combination selected by client
- **client_request**: Original client requirements
- **workflow_status**: Current workflow state

### Output Products
- **extended_task_list**: Comprehensive task data structure
  - tasks: List of ExtendedTask objects
  - processing_summary: Processing metrics
  - metadata: Additional context

### Downstream Consumers
- **Blueprint Generation Node**: Uses extended_task_list for comprehensive planning

## Error Handling Flow

```mermaid
graph TD
    A[Error Occurs] --> B{Error Type}
    
    B -->|Missing Timeline| C[Log Warning]
    C --> D[Skip Processing]
    D --> E[Continue to Blueprint]
    
    B -->|Agent Error| F[Catch Exception]
    F --> G[Log Error]
    G --> H[Update error_count]
    H --> I[Set last_error]
    I --> E
    
    B -->|Processing Failure| J[Catch Exception]
    J --> K[Log Error]
    K --> L[Update error_count]
    L --> M[Set last_error]
    M --> E
    
    E --> N[Workflow Continues]
    
    style A fill:#FFB6C1,stroke:#DC143C,stroke-width:2px
    style E fill:#90EE90,stroke:#006400,stroke-width:2px
    style N fill:#90EE90,stroke:#006400,stroke-width:2px
```

## Conditional Execution Logic

```python
def should_run_task_management(state: EventPlanningState) -> bool:
    """
    Conditions for running task management:
    1. timeline_data must be present
    2. workflow_status must not be FAILED
    """
    has_timeline = state.get('timeline_data') is not None
    is_failed = state.get('workflow_status') == WorkflowStatus.FAILED.value
    
    return has_timeline and not is_failed
```

## Key Features

### 1. Graceful Degradation
- Workflow continues even if task management fails
- Blueprint generation can work without extended_task_list
- Errors are logged but don't block progress

### 2. Conditional Execution
- Automatically skips if timeline data is missing
- Checks workflow status before processing
- Logs reasons for skipping

### 3. State Management
- Uses existing StateManager for persistence
- Follows existing state transition patterns
- Comprehensive logging of all transitions

### 4. Error Tracking
- Increments error_count on failures
- Stores error messages in last_error
- Logs detailed error information

### 5. Async Support
- Properly handles async agent processing
- Uses asyncio.run() for async method calls
- Maintains workflow synchronous interface

## Performance Considerations

### Processing Time
- Task management adds processing time to workflow
- Typical processing: 1-5 seconds depending on task complexity
- Async processing prevents blocking

### Memory Usage
- Extended task list stored in state
- State manager handles persistence
- Memory-efficient data structures

### Scalability
- Handles large task lists efficiently
- Parallel processing in sub-agents
- Tool execution optimized

## Monitoring and Observability

### Logging Points
1. Node entry with input data
2. Timeline data validation
3. Agent instantiation
4. Processing start/completion
5. Error occurrences
6. Node exit with output data

### Metrics Available
- Processing time (in processing_summary)
- Total tasks processed
- Tasks with errors
- Tasks with warnings
- Success/failure status

### State Transitions
All transitions logged with:
- Node name
- Input data
- Output data
- Success status
- Timestamp
