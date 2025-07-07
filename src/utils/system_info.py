import psutil
import platform
import os
from datetime import datetime
from typing import Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SystemInfoCollector:
    """시스템 정보 수집 클래스"""
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """전체 시스템 정보 수집"""
        try:
            return {
                "timestamp": datetime.now().isoformat(),
                "system": SystemInfoCollector._get_system_info(),
                "cpu": SystemInfoCollector._get_cpu_info(),
                "memory": SystemInfoCollector._get_memory_info(),
                "disk": SystemInfoCollector._get_disk_info(),
                "network": SystemInfoCollector._get_network_info(),
                "process": SystemInfoCollector._get_process_info(),
                "docker": SystemInfoCollector._get_docker_info()
            }
        except Exception as e:
            logger.error(f"시스템 정보 수집 중 오류 발생: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": f"시스템 정보 수집 실패: {str(e)}"
            }
    
    @staticmethod
    def _get_system_info() -> Dict[str, Any]:
        """시스템 기본 정보"""
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node(),
            "python_version": platform.python_version()
        }
    
    @staticmethod
    def _get_cpu_info() -> Dict[str, Any]:
        """CPU 정보"""
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        return {
            "usage_percent": cpu_percent,
            "count": cpu_count,
            "frequency_mhz": cpu_freq.current if cpu_freq else None,
            "frequency_max_mhz": cpu_freq.max if cpu_freq else None,
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
    
    @staticmethod
    def _get_memory_info() -> Dict[str, Any]:
        """메모리 정보"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "usage_percent": memory.percent,
            "swap_total_gb": round(swap.total / (1024**3), 2),
            "swap_used_gb": round(swap.used / (1024**3), 2),
            "swap_usage_percent": swap.percent
        }
    
    @staticmethod
    def _get_disk_info() -> Dict[str, Any]:
        """디스크 정보"""
        disk_usage = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        return {
            "total_gb": round(disk_usage.total / (1024**3), 2),
            "used_gb": round(disk_usage.used / (1024**3), 2),
            "free_gb": round(disk_usage.free / (1024**3), 2),
            "usage_percent": round((disk_usage.used / disk_usage.total) * 100, 2),
            "read_bytes": disk_io.read_bytes if disk_io else 0,
            "write_bytes": disk_io.write_bytes if disk_io else 0,
            "read_count": disk_io.read_count if disk_io else 0,
            "write_count": disk_io.write_count if disk_io else 0
        }
    
    @staticmethod
    def _get_network_info() -> Dict[str, Any]:
        """네트워크 정보"""
        network_io = psutil.net_io_counters()
        network_connections = len(psutil.net_connections())
        
        return {
            "bytes_sent": network_io.bytes_sent,
            "bytes_recv": network_io.bytes_recv,
            "packets_sent": network_io.packets_sent,
            "packets_recv": network_io.packets_recv,
            "active_connections": network_connections
        }
    
    @staticmethod
    def _get_process_info() -> Dict[str, Any]:
        """현재 프로세스 정보"""
        current_process = psutil.Process()
        
        return {
            "pid": current_process.pid,
            "name": current_process.name(),
            "cpu_percent": current_process.cpu_percent(),
            "memory_mb": round(current_process.memory_info().rss / (1024**2), 2),
            "memory_percent": current_process.memory_percent(),
            "num_threads": current_process.num_threads(),
            "create_time": datetime.fromtimestamp(current_process.create_time()).isoformat()
        }
    
    @staticmethod
    def _get_docker_info() -> Dict[str, Any]:
        """Docker 환경 정보"""
        docker_info = {
            "is_docker": False,
            "container_id": None,
            "image": None
        }
        
        try:
            # Docker 환경 확인
            if os.path.exists('/.dockerenv'):
                docker_info["is_docker"] = True
            
            # 컨테이너 ID 확인 (cgroup에서)
            if os.path.exists('/proc/self/cgroup'):
                with open('/proc/self/cgroup', 'r') as f:
                    for line in f:
                        if 'docker' in line:
                            parts = line.strip().split('/')
                            if len(parts) > 2:
                                docker_info["container_id"] = parts[-1][:12]  # 짧은 ID
                            break
            
            # 환경변수에서 Docker 정보 확인
            docker_info["image"] = os.getenv('DOCKER_IMAGE', None)
            
        except Exception as e:
            logger.debug(f"Docker 정보 수집 중 오류: {e}")
        
        return docker_info
    
    @staticmethod
    def get_simple_status() -> Dict[str, Any]:
        """간단한 상태 정보 (헬스체크용)"""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2)
            }
        except Exception as e:
            logger.error(f"상태 정보 수집 중 오류: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            } 