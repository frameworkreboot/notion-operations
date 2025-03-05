# Notion-CrewAI Integration

A background service that monitors a Notion database for tasks, processes them using CrewAI, and updates the results.

## Features

- Automatically processes tasks marked with "Execute" status in Notion
- Uses CrewAI for intelligent task processing
- Supports specialized research crew for in-depth analysis
- Updates Notion with detailed results and thought process

## Setup

### Prerequisites

- Python 3.10+
- A Notion integration with appropriate permissions
- OpenAI API key
- Serper API key (for research capabilities)

### Installation

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with the following variables:
   ```
   NOTION_API_KEY=your_notion_api_key
   OPENAI_API_KEY=your_openai_api_key
   SERPER_API_KEY=your_serper_api_key
   DATABASE_ID=your_notion_database_id
   ```

### Running Locally

```bash
python scheduled_service.py
```

## Usage

1. Create a task in your Notion database
2. Set its status to "Execute"
3. The service will:
   - Change the status to "In progress"
   - Process the task
   - Update the page with results
   - Change the status to "Review"

## Project Structure

```
notion-orchestrator/
├── .env
├── README.md
├── requirements.txt
├── orchestrator/
│   ├── __init__.py
│   ├── main.py
│   ├── webhook_handler.py
│   └── notion_api.py
├── manager_agent/
│   ├── __init__.py
│   └── task_router.py
└── tests/
    ├── test_orchestrator.py
    ├── test_manager_agent.py
    └── test_crews.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Documentation

The project documentation is built using Sphinx. To build the documentation:

1. Install the documentation dependencies:
   ```
   pip install sphinx sphinx-rtd-theme
   ```

2. Build the HTML documentation:
   ```
   cd docs
   .\make.bat html
   ```

3. Open the documentation in your browser:
   ```
   start build\html\index.html
   ```