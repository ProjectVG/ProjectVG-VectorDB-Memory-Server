from fastapi import APIRouter, HTTPException
from src.utils.system_info import SystemInfoCollector
from datetime import datetime
from src.utils.logger import get_logger

logger = get_logger(__name__)

system_router = APIRouter(prefix="/api/v1/system", tags=["system"])

@system_router.get("/info")
async def get_system_info():
    """전체 시스템 정보를 반환하는 엔드포인트"""
    logger.info("시스템 정보 요청 받음")
    try:
        system_info = SystemInfoCollector.get_system_info()
        return system_info
    except Exception as e:
        logger.error(f"시스템 정보 수집 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"시스템 정보 수집 실패: {str(e)}")

@system_router.get("/status")
async def get_system_status():
    """간단한 시스템 상태를 반환하는 엔드포인트 (헬스체크용)"""
    logger.info("시스템 상태 요청 받음")
    try:
        status = SystemInfoCollector.get_simple_status()
        return status
    except Exception as e:
        logger.error(f"시스템 상태 수집 중 오류: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@system_router.get("/cpu")
async def get_cpu_info():
    """CPU 정보만 반환하는 엔드포인트"""
    logger.info("CPU 정보 요청 받음")
    try:
        cpu_info = SystemInfoCollector._get_cpu_info()
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": cpu_info
        }
    except Exception as e:
        logger.error(f"CPU 정보 수집 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"CPU 정보 수집 실패: {str(e)}")

@system_router.get("/memory")
async def get_memory_info():
    """메모리 정보만 반환하는 엔드포인트"""
    logger.info("메모리 정보 요청 받음")
    try:
        memory_info = SystemInfoCollector._get_memory_info()
        return {
            "timestamp": datetime.now().isoformat(),
            "memory": memory_info
        }
    except Exception as e:
        logger.error(f"메모리 정보 수집 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"메모리 정보 수집 실패: {str(e)}")

@system_router.get("/disk")
async def get_disk_info():
    """디스크 정보만 반환하는 엔드포인트"""
    logger.info("디스크 정보 요청 받음")
    try:
        disk_info = SystemInfoCollector._get_disk_info()
        return {
            "timestamp": datetime.now().isoformat(),
            "disk": disk_info
        }
    except Exception as e:
        logger.error(f"디스크 정보 수집 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"디스크 정보 수집 실패: {str(e)}") 