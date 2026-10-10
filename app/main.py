import httpx
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from app.core.config import settings
from app.utils.security import validate_api_secret, generate_api_secret
from app.services.docker_service import docker_service
import os
import httpx

app = FastAPI(title="Bridge API Gateway")

# Request model for validation
class ExecutionRequest(BaseModel):
    type: str = Field(..., pattern="^(LuaScript|LuaFile|Pipeline)$")
    script: str = Field(..., max_length=10000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Bridge API Gateway is running. Use /docs for API documentation."}

@app.post("/auth/generate-secret", dependencies=[Depends(validate_admin_key)])
async def create_secret():
    """Generates a new API secret and updates the .env file. 
    Requires the Master Admin Key.
    """
    new_secret = generate_api_secret()
    # In a real production app, this would update a database or AWS Secrets Manager
    # For this tool, we update the .env file
    try:
        with open(".env", "r") as f:
            lines = f.readlines()
        
        with open(".env", "w") as f:
            for line in lines:
                if line.startswith("API_SECRET="):
                    f.write(f"API_SECRET={new_secret}\n")
                else:
                    f.write(line)
        
        # Update the running settings object so the change is immediate
        settings.API_SECRET = new_secret
        
        return {"new_secret": new_secret, "message": "API secret generated and applied successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save secret: {str(e)}")

@app.post("/service/start", dependencies=[Depends(validate_api_secret)])
async def start_service():
    container_id = docker_service.start_engine()
    return {"message": "Engine started successfully", "container_id": container_id}

@app.post("/service/stop", dependencies=[Depends(validate_api_secret)])
async def stop_service():
    docker_service.stop_engine()
    return {"message": "Engine stopped successfully"}

@app.get("/service/status", dependencies=[Depends(validate_api_secret)])
async def get_status():
    return docker_service.get_status()

@app.post("/execute", dependencies=[Depends(validate_api_secret)])
async def execute_script(payload: ExecutionRequest):
    """
    Proxies the execution request to the C++ engine.
    Supports:
    - Lua scripts (via LuaScript)
    - Lua files (via LuaFile - expects filename in 'script' field)
    - OGDF operations (via the engine's internal bindings)
    """
    # AUTO-START: Check if engine is running, if not, try to start it
    status = docker_service.get_status()
    if status["status"] != "running":
        try:
            docker_service.start_engine()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Engine was stopped and failed to auto-start: {str(e)}")

    async with httpx.AsyncClient() as client:
        try:
            # The C++ engine is the one that actually executes the OGDF/Lua logic
            response = await client.post(
                f"http://localhost:{settings.ENGINE_PORT}/execute", 
                json=payload.dict(),
                timeout=60.0 
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Engine unreachable: {str(e)}")

@app.get("/files/list", dependencies=[Depends(validate_api_secret)])
async def list_predefined_files():
    """Lists all predefined scripts and configuration files available in storage."""
    if not os.path.exists(settings.FILES_STORAGE_PATH):
        return {"files": [], "message": "Storage directory not found."}
    
    try:
        files = os.listdir(settings.FILES_STORAGE_PATH)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@app.get("/files/read/{filename}", dependencies=[Depends(validate_api_secret)])
async def read_predefined_file(filename: str):
    """Reads the content of a specific predefined file for the frontend."""
    # SECURITY: Prevent path traversal
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(settings.FILES_STORAGE_PATH, safe_filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"filename": safe_filename, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

@app.post("/files/load", dependencies=[Depends(validate_api_secret)])
async def load_files(file: UploadFile = File(...)):
    """Saves a predefined file to the storage path with path traversal protection."""
    os.makedirs(settings.FILES_STORAGE_PATH, exist_ok=True)
    
    # SECURITY: Sanitize filename to prevent path traversal attacks
    safe_filename = os.path.basename(file.filename)
    file_path = os.path.join(settings.FILES_STORAGE_PATH, safe_filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    return {"message": f"File {safe_filename} loaded successfully", "path": file_path}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.GATEWAY_PORT)
