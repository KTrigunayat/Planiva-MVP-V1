# Event Planning Agent v2

A modernized AI-powered event planning system built with CrewAI, LangGraph, and MCP servers for enhanced multi-agent collaboration and workflow orchestration.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

This system transforms event planning into an intelligent, collaborative process using multiple AI agents that work together to create optimal event combinations. The modernized architecture leverages cutting-edge AI orchestration frameworks while preserving all core business logic from the original system.

### Key Features

- **🤖 Multi-Agent Collaboration**: Five specialized AI agents working in harmony
- **🔄 Workflow Orchestration**: LangGraph-powered state management with beam search optimization
- **🔌 MCP Integration**: Enhanced capabilities through Model Context Protocol servers
- **⚡ Modern API**: FastAPI with async support and comprehensive documentation
- **📊 Advanced Monitoring**: Prometheus metrics, Grafana dashboards, and structured logging
- **🐳 Container-Ready**: Full Docker support with multi-environment configurations
- **🔒 Security-First**: Built-in authentication, rate limiting, and security headers

### Architecture Components

- **CrewAI**: Multi-agent framework for coordinated AI collaboration
- **LangGraph**: Workflow orchestration with state management and beam search
- **MCP Servers**: Enhanced capabilities through Model Context Protocol integration
- **FastAPI**: Modern REST API with async support and automatic documentation
- **PostgreSQL**: Robust data persistence with JSONB support and vector extensions
- **Ollama**: Local LLM inference for Gemma-2B and TinyLLaMA models
- **Prometheus & Grafana**: Comprehensive monitoring and observability

## 🏗️ System Architecture

The system consists of five specialized agents working in a coordinated workflow:

### Agent Roles

1. **🎭 Orchestrator Agent**: Master coordinator managing workflow and beam search optimization
2. **💰 Budgeting Agent**: Financial optimization and fitness score calculation using Gemma-2B
3. **🔍 Sourcing Agent**: Vendor procurement and qualification using TinyLLaMA
4. **⏰ Timeline Agent**: Logistics coordination and conflict detection
5. **📋 Blueprint Agent**: Final document generation and professional formatting

### Workflow Process

```mermaid
graph TB
    A[Client Request] --> B[Orchestrator Agent]
    B --> C[Budget Allocation]
    C --> D[Vendor Sourcing]
    D --> E[Beam Search Optimization]
    E --> F{More Iterations?}
    F -->|Yes| D
    F -->|No| G[Timeline Validation]
    G --> H[Blueprint Generation]
    H --> I[Final Delivery]
```

## Quick Start

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- PostgreSQL 16+ (or use Docker)
- Ollama (for local LLM inference)

### Installation

1. **Clone and setup the project:**
   ```bash
   git clone <repository-url>
   cd event_planning_agent_v2
   ```

2. **Create environment file:**
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Start with Docker Compose:**
   ```bash
   cd docker
   docker-compose up -d
   ```

### Development Setup

1. **Install development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

2. **Setup pre-commit hooks:**
   ```bash
   pre-commit install
   ```

3. **Run tests:**
   ```bash
   pytest
   ```

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database
DATABASE_URL=postgresql://eventuser:eventpass@localhost:5432/eventdb

# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
GEMMA_MODEL=gemma:2b
TINYLLAMA_MODEL=tinyllama

# CrewAI Settings
CREW_VERBOSE=true
CREW_MAX_ITERATIONS=10

# LangGraph Settings
BEAM_WIDTH=3
MAX_WORKFLOW_ITERATIONS=20

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
```

### MCP Server Configuration

Configure MCP servers in `config/mcp_config.json`:

```json
{
  "mcpServers": {
    "vendor-data-server": {
      "command": "uvx",
      "args": ["event-planning-vendor-server@latest"],
      "autoApprove": ["enhanced_vendor_search", "vendor_compatibility_check"]
    }
  }
}
```

## API Usage

### Create Event Plan

```bash
POST /v1/plans
Content-Type: application/json

{
  "client_id": "client123",
  "event_type": "wedding",
  "guest_count": 150,
  "budget": 50000,
  "date": "2024-06-15",
  "preferences": {
    "style": "elegant",
    "dietary_restrictions": ["vegetarian", "gluten-free"]
  }
}
```

### Get Plan Status

```bash
GET /v1/plans/{plan_id}
```

### Select Combination

```bash
POST /v1/plans/{plan_id}/select-combination
Content-Type: application/json

{
  "combination_id": "combo123"
}
```

## Development

### Project Structure

```
event_planning_agent_v2/
├── agents/          # CrewAI agents
├── workflows/       # LangGraph workflows
├── tools/           # CrewAI tools
├── mcp_servers/     # MCP server implementations
├── database/        # Database models and migrations
├── api/             # FastAPI routes and schemas
├── config/          # Configuration management
├── tests/           # Test suite
└── docker/          # Docker configuration
```

### Running Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Performance tests
pytest tests/performance/

# All tests with coverage
pytest --cov=event_planning_agent_v2
```

### Code Quality

```bash
# Format code
black event_planning_agent_v2/

# Lint code
flake8 event_planning_agent_v2/

# Type checking
mypy event_planning_agent_v2/
```

## Monitoring

### Prometheus Metrics

Access metrics at `http://localhost:9090`

### Grafana Dashboards

Access dashboards at `http://localhost:3000` (admin/admin)

### Health Checks

```bash
GET /health
GET /metrics
```

## Deployment

### Docker Deployment

```bash
# Build and run
docker-compose -f docker/docker-compose.yml up -d

# Scale services
docker-compose up -d --scale event-planning-api=3
```

### Production Configuration

1. Update `.env` with production values
2. Configure proper secrets management
3. Setup SSL/TLS certificates
4. Configure load balancing
5. Setup monitoring and alerting

## Migration from v1

The system maintains API compatibility with the original Event Planning Agent. Existing integrations should work without modification.

### Data Migration

```bash
# Run migration scripts
python -m event_planning_agent_v2.database.migrations migrate
```

## Troubleshooting

### Common Issues

1. **Ollama Connection Issues**
   - Ensure Ollama is running: `ollama serve`
   - Check model availability: `ollama list`

2. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check connection string in `.env`

3. **MCP Server Issues**
   - Verify uvx installation: `uvx --version`
   - Check MCP server logs in Docker

### Logs

```bash
# Application logs
tail -f logs/event_planning.log

# Docker logs
docker-compose logs -f event-planning-api
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run quality checks
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: [docs-url]
- Email: team@eventplanning.ai