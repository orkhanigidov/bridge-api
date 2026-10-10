# Bridge API Gateway

A secure, lightweight Python backend designed to orchestrate and proxy requests to the C++ Bridge Engine. This service manages the lifecycle of the engine container, handles API security, and provides a RESTful interface for executing Lua scripts and OGDF C++ operations.

## 🚀 Architecture

The system follows a Gateway pattern:
**Frontend** -> **FastAPI Gateway** -> **Docker Engine (C++ Bridge Engine)** -> **OGDF/Lua Execution**

## ✨ Features

- **Container Orchestration**: Automatically pulls the latest engine image from GHCR and manages the container lifecycle.
- **Secure Access**: API Secret validation via `X-API-SECRET` header.
- **Dynamic Secret Generation**: Endpoint to generate and rotate API keys on the fly.
- **File Management**: Securely upload predefined files to be mounted into the engine's runtime environment.
- **Resource Guarding**: Implements CPU and Memory limits on the engine container to prevent DoS attacks.
- **CORS Enabled**: Ready for integration with modern web frontends.

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- Docker Engine installed and running
- Access to the GitHub Container Registry (GHCR)

### Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd bridge-api
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env to set your GHCR_IMAGE and ports
   ```

4. Start the gateway:
   ```bash
   python app/main.py
   ```

## 📡 API Reference

### Authentication
| Endpoint | Method | Header | Description |
| :--- | :--- | :--- | :--- |
| `/auth/generate-secret` | `POST` | None | Generates a new API secret key |

### Service Management
| Endpoint | Method | Header | Description |
| :--- | :--- | :--- | :--- |
| `/service/start` | `POST` | `X-API-SECRET` | Pulls and starts the C++ engine |
| `/service/stop` | `POST` | `X-API-SECRET` | Stops the engine container |
| `/service/status` | `GET` | `X-API-SECRET` | Checks engine health |

### Execution & Data
| Endpoint | Method | Header | Description |
| :--- | :--- | :--- | :--- |
| `/execute` | `POST` | `X-API-SECRET` | Executes Lua/OGDF code |
| `/files/load` | `POST` | `X-API-SECRET` | Uploads predefined files |
| `/files/list` | `GET` | `X-API-SECRET` | Lists available predefined files |
| `/files/read/{filename}` | `GET` | `X-API-SECRET` | Retrieves content of a specific file |

## 🔒 Security Considerations

- **Sandboxing**: The C++ engine runs as a non-root user inside a container.
- **Input Validation**: All requests are validated using Pydantic models to prevent injection.
- **Path Traversal**: Filenames are sanitized using `os.path.basename` before saving.
- **Resource Limits**: Containers are capped at 1GB RAM and 0.5 CPU.

## ☁️ AWS Deployment (Minimal Workload)

For the leanest deployment:
1. Use **AWS Lightsail** (VPS).
2. Install Docker and Python.
3. Run the gateway and engine using the provided configuration.
4. Use an AWS Application Load Balancer (ALB) or CloudFront to provide HTTPS.
