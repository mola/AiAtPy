# AiAtPy

## Overview
A system that detects logical paradoxes between new Iranian laws and existing legislation using AI. Features:
- Secure API for law submission
- Parallel comparison engine
- Multi-LLM support
- Law version tracking

## Project Structure
```
iran-law-analyzer/
├── main.py                  # Application entry point
├── app_manager.py           # Core coordinator (Qt signals/slots)
├── flask_server/            # Web API implementation
│   ├── routes.py            # API endpoint definitions
│   └── auth.py              # User authentication
├── database/                # Law database management
│   ├── models.py            # Data models (Law, User)
│   ├── crud.py              # Database operations (Create/Read/Update/Delete)
│   └── session.py           # Database connection handler
├── llm_connectors/          # AI model integrations
│   ├── base_connector.py    # Common LLM interface
│   └── [provider]_connector.py # Specific LLM implementations
├── pipeline/                # Core analysis logic
│   ├── paradox_detector.py  # Main comparison controller
│   └── comparison_task.py   # Parallel comparison units
├── utils/                   # Helper modules
│   ├── config.py            # Configuration loader
│   ├── logger.py            # Logging setup
│   └── qthread_pool.py      # Thread management
└── requirements.txt         # Python dependencies
```

## Workflow Pipeline
1. **User Submission**  
   User submits new law via API with category/date filters
   
2. **Database Query**  
   System retrieves relevant existing laws
   
3. **Parallel Comparison**  
   For each existing law:
   - Creates comparison task
   - Assigns to LLM connector
   - Runs in separate thread
   
4. **Paradox Detection**  
   LLMs analyze logical conflicts between:
   - Submitted law
   - Each existing law
   
5. **Result Compilation**  
   System aggregates results and returns:
   - Conflict status
   - Affected laws
   - Reasoning excerpts

## Future Roadmap
- Phase 2: Add RAG for legal Q&A
- Phase 3: Historical amendment tracking
- Phase 4: Cluster analysis of related laws