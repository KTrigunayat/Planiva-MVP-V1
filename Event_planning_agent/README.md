# Planiva - AI-Powered Event Planning System

A streamlined AI system that automates vendor sourcing and recommendations for weddings and events using intelligent filtering and ranking algorithms.

## 🌟 Features

- **Smart Filtering**: Extracts hard requirements and soft preferences from client data
- **Intelligent Ranking**: Combines budget optimization with preference matching
- **Multi-Service Support**: Venues, caterers, photographers, makeup artists
- **Budget-Aware**: Respects budget constraints while maximizing value
- **Simple Architecture**: Clean, maintainable codebase without complex dependencies
- **Fast Performance**: Direct database queries with efficient scoring algorithms

## 🏗️ Architecture

### Core Components

1. **Simple Workflow**: Streamlined vendor sourcing process
2. **Hybrid Filtering**: Deterministic hard filters + AI-powered soft preferences  
3. **Database Integration**: Direct PostgreSQL queries with intelligent ranking
4. **Preference Matching**: Text-based matching for client vision alignment

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL with pgvector extension
- Ollama (for local LLM inference)

### Installation

1. **Clone and setup**:
```bash
cd Event_planning_agent
python setup.py
```

2. **Configure environment**:
Edit `.env` file with your database credentials:
```env
DB_NAME=planiva_events
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

3. **Test the system**:
```bash
python test_system.py
```

4. **Run demo**:
```bash
python demo.py
```

### Database Management

The system includes database management tools:

```bash
# Show database statistics
python manage_database.py stats

# Clean and reload all data
python manage_database.py reload

# Reload specific service type
python manage_database.py reload-venues

# Create backup
python manage_database.py backup
```

## 📊 Data Structure

The system uses JSON data from the `Data_JSON` folder:

- `correct_venue_data.json` - Wedding venues with capacity, pricing, amenities
- `correct_caterers_data.json` - Catering services with cuisine types, pricing
- `photographers_data.json` - Photography services with packages, styles
- `Makeup_artist.json` - Makeup artists with services, pricing

## 🔧 Usage

### Basic Usage

```python
from simple_workflow import SimpleVendorSourcing

# Initialize the sourcing system
sourcing = SimpleVendorSourcing()

# Define client requirements
client_data = {
    "clientName": "John & Jane",
    "guestCount": {"Reception": 200},
    "clientVision": "Modern elegant wedding in Bangalore",
    "budget": 500000
}

# Get venue recommendations
venues = sourcing.source_vendors("venue", client_data)
print(venues)
```

### Advanced Filtering

The system automatically extracts:

**Hard Filters** (Must-have requirements):
- Budget constraints
- Location preferences  
- Capacity requirements
- Essential amenities

**Soft Preferences** (Nice-to-have):
- Style preferences
- Theme matching
- Cuisine preferences
- Service quality indicators

## 🧪 Testing

Run system tests:

```bash
# Quick system test
python test_system.py

# Test specific functionality
python simple_workflow.py
```

## 📈 Performance

- **Response Time**: ~1-2 seconds per service type
- **Accuracy**: Intelligent preference matching with budget optimization
- **Scalability**: Handles 1000+ vendors per service type
- **Reliability**: Simple architecture with minimal dependencies

## 🔍 How It Works

1. **Client Input**: Wedding requirements, preferences, and budget
2. **Filter Generation**: AI extracts hard filters and soft preferences
3. **Database Query**: SQL filters candidates by hard requirements
4. **Semantic Ranking**: Vector similarity matches client vision to vendor descriptions
5. **Composite Scoring**: Combines price optimization with preference matching
6. **Recommendations**: Returns top 5 ranked vendors with explanations

## 🛠️ Configuration

### Service Type Weights

Adjust preference vs. price importance in `event_tools.py`:

```python
TABLE_CONFIG = {
    'venue': {'weights': {'price': 0.7, 'preference': 0.3}},
    'caterer': {'weights': {'price': 0.6, 'preference': 0.4}},
    'photographer': {'weights': {'price': 0.4, 'preference': 0.6}},
    'makeup_artist': {'weights': {'price': 0.5, 'preference': 0.5}}
}
```

## 📁 File Structure

```
Event_planning_agent/
├── README.md                # This file
├── setup.py                # Automated setup script
├── database_setup.py       # Database schema and data loading
├── event_tools.py          # Core filtering and ranking tools
├── simple_workflow.py      # Main vendor sourcing workflow
├── test_system.py          # System test suite
├── demo.py                 # Interactive demo script
├── manage_database.py      # Database management utilities
├── requirements.txt        # Python dependencies
├── .env.template          # Environment configuration template
└── .env                   # Your environment configuration
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

**Database Connection Failed**:
- Check PostgreSQL is running
- Verify credentials in `.env` file
- Ensure database exists: `createdb planiva_events`

**Ollama Models Not Found**:
- Install Ollama: https://ollama.ai/
- Pull models: `ollama pull nomic-embed-text && ollama pull gemma:2b`

**Import Errors**:
- Install requirements: `pip install -r requirements.txt`
- Check Python version: `python --version` (need 3.8+)

**No Vendors Found**:
- Run database setup: `python database_setup.py`
- Check data files exist in `../Data_JSON/`
- Verify budget is reasonable for service type

### Performance Issues

**Slow Responses**:
- Generate embeddings first: `python embed_data.py`
- Use smaller embedding model
- Reduce similarity search results

**Memory Usage**:
- Use lighter LLM model: `gemma:2b` instead of larger models
- Reduce batch sizes in embedding generation

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Run the test suite to identify specific problems
3. Review logs for detailed error messages
4. Open an issue with system details and error logs

---

Built with ❤️ using LangGraph, CrewAI, and LlamaIndex