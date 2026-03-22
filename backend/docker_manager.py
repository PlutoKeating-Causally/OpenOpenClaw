import docker
from docker.errors import NotFound, APIError
import subprocess
import json
import os
import platform

class DockerManager:
    def __init__(self):
        self.client = self._init_docker_client()
    
    def _init_docker_client(self):
        try:
            return docker.from_env()
        except:
            if platform.system() == "Windows":
                try:
                    return docker.DockerClient(base_url='npipe:////./pipe/docker_engine')
                except:
                    return None
            return None
    
    def load_env_file(self, env_file_path: str) -> dict:
        env_vars = {}
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        return env_vars
    
    def create_network(self, network_name: str):
        try:
            self.client.networks.get(network_name)
        except NotFound:
            self.client.networks.create(
                network_name,
                driver="bridge",
                attachable=True
            )
    
    def remove_network(self, network_name: str):
        try:
            network = self.client.networks.get(network_name)
            network.remove()
        except NotFound:
            pass
    
    def list_networks(self):
        try:
            return [{"name": n.name, "id": n.id} for n in self.client.networks.list()]
        except:
            return []
    
    def run_container(self, name: str, network: str, ports: dict, volumes: dict, 
                      image: str = "openclaw/openclaw:latest", environment: dict = None):
        if self.client is None:
            raise Exception("Docker client not initialized")
        
        try:
            existing = self.client.containers.get(name)
            if existing.status == "running":
                return existing
            else:
                existing.remove()
        except NotFound:
            pass
        
        port_bindings = {}
        for container_port, host_port in ports.items():
            port_bindings[container_port] = [{"HostPort": str(host_port)}]
        
        volume_binds = {}
        for host_path, bind_config in volumes.items():
            volume_binds[host_path] = {
                "bind": bind_config["bind"],
                "mode": bind_config.get("mode", "rw")
            }
        
        env = environment or []
        if isinstance(env, dict):
            env = [f"{k}={v}" for k, v in env.items()]
        
        container = self.client.containers.run(
            image=image,
            name=name,
            network=network,
            ports=port_bindings,
            volumes=volume_binds,
            environment=env,
            detach=True,
            remove=False,
            user="root"
        )
        
        return container
    
    def stop_container(self, name: str):
        try:
            container = self.client.containers.get(name)
            container.stop(timeout=10)
        except NotFound:
            pass
    
    def start_container(self, name: str):
        try:
            container = self.client.containers.get(name)
            container.start()
        except NotFound:
            raise Exception(f"Container {name} not found")
    
    def restart_container(self, name: str):
        try:
            container = self.client.containers.get(name)
            container.restart(timeout=10)
        except NotFound:
            raise Exception(f"Container {name} not found")
    
    def remove_container(self, name: str):
        try:
            container = self.client.containers.get(name)
            container.stop(timeout=5)
            container.remove(force=True)
        except NotFound:
            pass
    
    def get_container_info(self, name: str) -> dict:
        try:
            container = self.client.containers.get(name)
            return {
                "id": container.id,
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else container.image.short_id,
                "status": container.status,
                "created": container.attrs.get("Created"),
                "state": container.attrs.get("State", {}).get("Status"),
                "ports": container.ports,
                "mounts": container.attrs.get("Mounts"),
                "networks": list(container.attrs.get("NetworkSettings", {}).get("Networks", {}).keys())
            }
        except NotFound:
            return {}
    
    def get_container_logs(self, name: str, tail: int = 100) -> str:
        try:
            container = self.client.containers.get(name)
            logs = container.logs(tail=tail, timestamps=True).decode("utf-8")
            return logs
        except NotFound:
            return ""
    
    def list_containers(self, all: bool = True) -> list:
        try:
            containers = self.client.containers.list(all=all)
            return [{
                "id": c.id,
                "name": c.name,
                "image": c.image.tags[0] if c.image.tags else c.image.short_id,
                "status": c.status,
                "state": c.attrs.get("State", {}).get("Status"),
                "created": c.attrs.get("Created")
            } for c in containers]
        except:
            return []
    
    def get_container_stats(self, name: str) -> dict:
        if self.client is None:
            return {"error": "Docker client not initialized"}
        try:
            container = self.client.containers.get(name)
            if container.status != "running":
                return {
                    "cpu_percent": 0,
                    "memory_usage": 0,
                    "memory_limit": 0,
                    "memory_percent": 0
                }
            stats = container.stats(stream=False)
            
            cpu_percent = 0
            memory_usage = 0
            memory_limit = 1
            memory_percent = 0
            
            try:
                cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                system_cpu_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
                
                if system_cpu_delta > 0:
                    percpu_usage = stats["cpu_stats"]["cpu_usage"].get("percpu_usage", [])
                    cpu_count = len(percpu_usage) if percpu_usage else 1
                    cpu_percent = (cpu_delta / system_cpu_delta) * cpu_count * 100
            except (KeyError, TypeError, ZeroDivisionError):
                pass
            
            try:
                memory_usage = stats["memory_stats"].get("usage", 0)
                memory_limit = stats["memory_stats"].get("limit", 1)
                if memory_limit > 0:
                    memory_percent = (memory_usage / memory_limit) * 100
            except (KeyError, TypeError, ZeroDivisionError):
                pass
            
            return {
                "cpu_percent": round(cpu_percent, 2),
                "memory_usage": memory_usage,
                "memory_limit": memory_limit,
                "memory_percent": round(memory_percent, 2)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_system_info(self) -> dict:
        try:
            info = self.client.info()
            return {
                "containers": info.get("Containers", 0),
                "containers_running": info.get("ContainersRunning", 0),
                "containers_paused": info.get("ContainersPaused", 0),
                "containers_stopped": info.get("ContainersStopped", 0),
                "images": info.get("Images", 0),
                "memory_total": info.get("MemTotal", 0),
                "cpus": info.get("NCPU", 0),
                "docker_version": info.get("ServerVersion", "unknown")
            }
        except:
            return {}
    
    def pull_image(self, image: str = "openclaw/openclaw:latest"):
        try:
            self.client.images.pull(image)
            return True
        except:
            return False
    
    def pull_image_stream(self, image: str = "openclaw/openclaw:latest"):
        """Pull an image and yield real-time progress lines as strings."""
        if self.client is None:
            yield "ERROR: Docker client not initialized"
            return

        try:
            # Parse image into repository and tag
            if ":" in image:
                repo, tag = image.rsplit(":", 1)
            else:
                repo, tag = image, "latest"

            yield f"$ docker pull {image}"
            
            # Use low-level API for streaming
            for chunk in self.client.api.pull(repo, tag=tag, stream=True, decode=True):
                status = chunk.get("status", "")
                progress = chunk.get("progress", "")
                layer_id = chunk.get("id", "")
                error = chunk.get("error", "")
                
                if error:
                    yield f"ERROR: {error}"
                    return
                
                if layer_id:
                    line = f"{layer_id}: {status}"
                    if progress:
                        line += f" {progress}"
                    yield line
                elif status:
                    yield status
            
            yield "Pull complete ✔"
        except Exception as e:
            yield f"ERROR: {str(e)}"
    
    def get_container_by_pattern(self, pattern: str) -> list:
        try:
            containers = self.client.containers.list(all=True)
            return [c for c in containers if pattern in c.name]
        except:
            return []
    
    def list_images(self) -> list:
        try:
            images = self.client.images.list()
            result = []
            for img in images:
                result.append({
                    "id": img.id,
                    "tags": img.tags,
                    "short_id": img.short_id,
                    "created": img.attrs.get("Created"),
                    "size": img.attrs.get("Size")
                })
            return result
        except:
            return []
