import docker
import logging
from app.core.config import settings
from fastapi import HTTPException

logger = logging.getLogger("bridge-api.docker")

class DockerService:
    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            logger.error(f"Docker client initialization failed: {e}")
            self.client = None

    def start_engine(self):
        if not self.client:
            raise HTTPException(status_code=500, detail="Docker daemon not available on host")

        try:
            logger.info(f"Pulling image {settings.GHCR_IMAGE}...")
            self.client.images.pull(settings.GHCR_IMAGE)
            
            self.stop_engine()

            logger.info("Starting bridge-engine container...")
            container = self.client.containers.run(
                settings.GHCR_IMAGE,
                detach=True,
                ports={f'8000/tcp': settings.ENGINE_PORT},
                volumes={settings.FILES_STORAGE_PATH: {'bind': '/app/data', 'mode': 'rw'}},
                name="bridge-engine",
                restart_policy={"Name": "always"},
                # Security: Limit resources to prevent DoS
                mem_limit="1g",
                cpu_period=100000,
                cpu_quota=50000 # 0.5 CPU
            )
            return container.id
        except Exception as e:
            logger.exception("Failed to start engine")
            raise HTTPException(status_code=500, detail=f"Failed to start engine: {str(e)}")

    def stop_engine(self):
        try:
            container = self.client.containers.get("bridge-engine")
            logger.info("Stopping bridge-engine container...")
            container.stop()
            container.remove()
        except docker.errors.NotFound:
            pass
        except Exception as e:
            logger.error(f"Error stopping engine: {e}")

    def get_status(self):
        try:
            container = self.client.containers.get("bridge-engine")
            return {
                "status": container.status,
                "id": container.short_id,
                "health": "healthy" if container.status == "running" else "unhealthy"
            }
        except docker.errors.NotFound:
            return {"status": "stopped", "health": "unhealthy"}
        except Exception as e:
            logger.exception("Error checking engine status")
            raise HTTPException(status_code=500, detail=f"Error checking status: {str(e)}")

docker_service = DockerService()
