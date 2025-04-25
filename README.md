# MCP Chain-of-Thought Calculator

A mathematical agent implementing chain-of-thought reasoning with verification capabilities.

## Core Concepts

### Chain of Thought (CoT)
- Implements explicit reasoning paths for complex calculations
- Benefits:
  - Traceable decision-making process
  - Error detection at intermediate steps
  - Ability to backtrack and correct mistakes
- Implementation:
  - Each step produces verifiable outputs
  - Results are chained through mathematical transformations
  - Verification at each transformation ensures reliability

### UV Package Management
- Modern Python packaging tool used for:
  - Automatic dependency resolution
  - Isolated virtual environments per project
  - Faster package installation (Rust-based)
- Project uses `uv run` for execution:
  - Handles dependencies on-the-fly
  - Maintains consistent environment
  - No manual requirements installation needed

### Verification Architecture
- Two-layer verification system:
  - Type verification: Ensures correct data types for operations
  - Value verification: Validates calculation results
- Adaptive tolerance handling:
  - Dynamic adjustment based on number magnitude
  - Preserves accuracy for both small and large computations
- Supports multiple data types:
  - Numeric (int, float) with appropriate precision
  - List operations with element-wise verification
  - String to numeric conversions with validation

## Project Setup

### Prerequisites
- Python 3.9 or higher
- UV package manager
- Gmail account with API access
- macOS for GUI features (optional)

### Installation Steps

1. Install UV (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone the repository:
```bash
git clone https://github.com/RohinSequeira/mcp_cot_prompting.git
cd mcp_cot_prompting
```

3. Set up Gmail API:
   - Go to Google Cloud Console
   - Create a new project
   - Enable Gmail API
   - Create credentials (OAuth 2.0 Client ID)
   - Download credentials as `credentials.json`
   - Place in project root directory

### Environment Setup

1. Create `.env` file:
```bash
# Create new .env file
touch .env

# Add the following content:
echo "GEMINI_API_KEY=your_gemini_api_key_here
EMAIL_ADDRESS=your_gmail_address@gmail.com" > .env
```

2. Update `.env` with your credentials:
   - Replace `your_gemini_api_key_here` with your Gemini API key
     - Get it from: https://makersuite.google.com/app/apikey
   - Replace `your_gmail_address@gmail.com` with your Gmail address
     - Must match the account used for Gmail API credentials

### Authentication Files

1. `credentials.json`:
   - Download from Google Cloud Console
   - Required for Gmail API access
   - Store in project root directory

2. `token.json`:
   - Auto-generated during first run
   - Handles Gmail API authentication
   - No manual creation needed
   - Self-refreshing when expired

### Running the Project

1. First run:
```bash
uv run talk2mcp-2.py
```
This will:
- Install all dependencies automatically
- Trigger Gmail OAuth flow in browser
- Generate `token.json`
- Start the application

2. Subsequent runs:
```bash
uv run talk2mcp-2.py
```

## Tool Categories

1. Math Tools
   - Input validation for integers/floats
   - Automatic type conversion
   - Result verification

2. System Tools
   - `verify`: Checks calculation accuracy
   - `show_reasoning`: Displays step-by-step logic

3. Email Tools
   - Send/read emails
   - Handle attachments
   - Manage email status

## Notes

- Verification uses relative tolerance for large numbers (>1e10)
- Email functionality requires valid Gmail API credentials
- GUI tools are macOS-specific

## Troubleshooting

Common issues:
- Token expired: Delete `token.json` and rerun
- Gmail API errors: Check credentials and permissions
- UV issues: Update UV to latest version
