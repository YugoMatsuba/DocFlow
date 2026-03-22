# Workflow Application

This is a workflow application that allows users to create and execute document processing pipelines using various node types.

## Project Structure

```
.
├── server/                 # FastAPI backend
│   ├── main.py            # FastAPI entry point
│   ├── models.py          # Pydantic models
│   ├── schemas.py         # Request/Response schemas
│   └── requirements.txt   # Python dependencies
├── client/                # React frontend
│   ├── src/
│   │   ├── App.tsx        # Main React component
│   │   ├── api.ts         # API client functions
│   │   ├── types.ts       # TypeScript type definitions
│   │   └── main.tsx       # React entry point
│   ├── index.html         # HTML template
│   ├── package.json       # Node dependencies
│   ├── tsconfig.json      # TypeScript configuration
│   └── vite.config.ts     # Vite configuration
├── spec.md                # Project requirements
└── README.md              # This file
```

## Setup Instructions

### Prerequisites

- **Python 3.8+** for the backend
- **Node.js 16+** and **npm** for the frontend

### Backend Setup

1. Navigate to the server directory:
   ```bash
   cd server
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI server:
   ```bash
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

The backend will be available at: http://localhost:8000

### Frontend Setup

1. Navigate to the client directory:
   ```bash
   cd client
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at: http://localhost:3000

## API Endpoints

### Workflows
- `POST /workflows` - Create a new workflow
- `GET /workflows/{wf_id}` - Get workflow details
- `POST /workflows/{wf_id}/nodes` - Add a node to workflow
- `POST /workflows/{wf_id}/run` - Execute workflow

### Supported Node Types
- `extract_text` - Extract text from documents
- `generative_ai` - Process text using AI/LLM
- `formatter` - Format text (uppercase, lowercase, etc.)

## Usage

1. Start both backend and frontend servers
2. Open http://localhost:3000 in your browser
3. Create a new workflow by entering a name
4. Add nodes to your workflow using the buttons
5. Run the workflow to see results

## Development

This is the base implementation from the spec. The application currently:
- Stores data in memory (not persistent)
- Runs workflows synchronously
- Provides basic node type implementations

Future enhancements will include:
- Database persistence
- Async workflow execution
- PDF upload and text extraction
- Advanced node configurations
- DAG structure support

## API Documentation

When the backend is running, visit http://localhost:8000/docs for interactive API documentation.