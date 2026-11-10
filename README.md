# India Bank Rates MCP Server

A Model Context Protocol (MCP) server designed for **Antigravity IDE** that empowers LLMs to dynamically fetch, parse, and analyze real-time interest rates and central bank policies directly from official banking portals.

## 🛠️ Core Tools Provided
* **`get_fd_rates` / `get_loan_rates`**: Fetches raw table matrices and filters targeted deposit yields or lending benchmarks (MCLR, RLLR, Home, Car) based on custom tenures or asset profiles.
* **`compare_fd_rates` / `compare_loan_rates`**: Runs comparative analytics across multiple portals, automatically sorting the highest potential returns based on parsed yield percentages.
* **`get_repo_rate`**: Tracks the Reserve Bank of India (RBI) policy framework to dynamically catch the prevailing monetary policy repo rate for macro-economic context.
* **`list_banks` & `refresh_sources`**: Manages sector targets (public vs. private) and flushes the in-memory cache for instant, zero-delay source refreshing.

---

## 🚀 Getting Started & Configuration

Follow these steps to set up and configure the MCP server with your IDE client.

### 1. Project Architecture
Create the core backbone files for the agent within your project directory:
* **`server.py`**: Contains the `FastMCP` initialization and rate-fetching tools.
* **`sources.py`**: Defines target data configurations (such as the `BANKS` schema and `RBI_SOURCES` links).

### 2. Environment Setup
Create a virtual environment (`venv`) to isolate dependencies and install the required packages:

```bash
# Create the virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install required packages
pip install mcp fastmcp httpx pandas bs4 lxml openpyxl
```

### 3. Client Configuration
To connect an MCP client like **Antigravity IDE** to your server, add the configuration mapping to your client settings file. 

Edit your local configuration file (e.g., `C:\Users\<Your-Username>\.gemini\config\mcp_config.json`) and append the following entry:

```json
{
  "mcpServers": {
    "india-bank-rates": {
      "command": "\\.venv\\Scripts\\python.exe",
      "args": ["-m", "india_bank_rates_mcp.server"],
      "cwd": project_directory
    }
  }
}
```
*Note: Ensure you update the absolute paths above to match your local repository's directory setup.*

### 4. Running & Testing the Server
Before verifying inside your IDE client, manually test the module in your terminal using the virtual environment interpreter to isolate syntax or module errors:

```bash
.venv\Scripts\python.exe -m india_bank_rates_mcp.server
```
*Note: If the command runs and produces a blank, continuous hanging prompt with no errors, your server is compiled correctly and actively listening for connection requests.*
