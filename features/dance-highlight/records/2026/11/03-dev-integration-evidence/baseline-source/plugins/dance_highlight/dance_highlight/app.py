"""안무 하이라이트 플러그인 구현."""

from __future__ import annotations

import json
import logging
import base64
import binascii
import gc
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from clipper_plugin_sdk import PluginBase
from clipper_plugin_sdk.base import CancelFlag
from clipper_plugin_sdk.models import JobRequest

from .services.config import detect_yolo_device, DanceConfig
from .services.pipeline import DancePipeline
from .services.pose_engine import PoseEngine
from .services.face_cluster import FaceClusterService
from .services.render import RenderService
from .services.dance_meta import DanceMetaBuilder

logger = logging.getLogger("dance_highlight")
MAX_REFERENCE_IMAGE_BYTES = 10 * 1024 * 1024


class ReferenceValidationRequest(BaseModel):
    imageBase64: str


class DanceHighlightPlugin(PluginBase):
    name = "dance_highlight"
    version = "0.1.0"

    def __init__(self) -> None:
        super().__init__()
        self._pipeline: DancePipeline | None = None
        self._device: str = "unknown"
        self._models_ready = False

    def load_models(self) -> None:
        config = DanceConfig()

        # current = 완료된 단계 수. 이벤트는 각 단계 시작 직전에 발행해
        # Angular가 "지금 이 모델을 설치 중"임을 표시할 수 있게 한다.
        self.print_model_loading("YOLO 포즈 모델 (yolov8s-pose.pt)", 0, 2)
        pose = PoseEngine(config)  # ultralytics → userData/yolov8s-pose.pt

        self.print_model_loading("얼굴 인식 모델 (YuNet/AuraFace)", 1, 2)
        face = FaceClusterService(config,cpu_only=True)

        self._pipeline = DancePipeline(
            config=config,
            pose=pose,
            face=face,
            render=RenderService(config),
            meta_builder=DanceMetaBuilder(config),
        )
        self._device = str(config.yolo_device)
        self._models_ready = True
        logger.info("DancePipeline ready (device=%s)", config.yolo_device)

    def get_runtime_accelerators(self) -> dict[str, Any]:
        return {
            "primary_device": self._device,
            "pipeline": "yolo_pose_opencv_face",
            "models": {"body_tracking": {"enabled": False, "reason": "disabled_runtime_cost"}},
        }

    def register_extra_routes(self, app: FastAPI) -> None:
        @app.post("/dance/reference/validate")
        def validate_reference(request: ReferenceValidationRequest):
            if self._pipeline is None and not self._models_ready:
                return JSONResponse(status_code=503, content={"error": "models_not_loaded"})
            with self.active_request():
                encoded = request.imageBase64
                if len(encoded) > ((MAX_REFERENCE_IMAGE_BYTES + 2) // 3) * 4 + 4:
                    return JSONResponse(status_code=413, content={"error": "image_too_large"})
                try:
                    image_bytes = base64.b64decode(encoded, validate=True)
                except (binascii.Error, ValueError):
                    return JSONResponse(status_code=400, content={"error": "invalid_base64"})
                if len(image_bytes) > MAX_REFERENCE_IMAGE_BYTES:
                    return JSONResponse(status_code=413, content={"error": "image_too_large"})
                if not image_bytes:
                    return {"faceDetected": False, "reason": "invalid_image"}
                try:
                    image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
                except cv2.error:
                    return {"faceDetected": False, "reason": "invalid_image"}
                if image is None:
                    return {"faceDetected": False, "reason": "invalid_image"}
                if self._pipeline is not None:
                    face=self._pipeline.face
                else:
                    # A separate CPU reference service never holds the analysis GPU.
                    face=FaceClusterService(DanceConfig(yolo_device='cpu'),cpu_only=True)
                if face.get_face_embedding(image) is None:
                    return {"faceDetected": False, "reason": "no_face"}
                return {"faceDetected": True}

    def run_job(self, request: JobRequest, cancel_flag: CancelFlag) -> dict[str, Any]:
        from clipper_accelerators.visual_unit import run_visual_unit
        from clipper_accelerators.errors import Cancelled
        video=request.params.get('video_path');root=request.params.get('output_root')
        if not video or not root:return {'error':'video_path and output_root are required'}
        if not Path(video).is_file():return {'error':f'video file not found: {video}'}
        device=self._device if self._device!='unknown' else detect_yolo_device()
        # Owned children create their own fresh models. Release the startup copy.
        self._pipeline=None
        gc.collect()
        try:
            return run_visual_unit(self.name,request.job_id,request.params,device,cancel_flag,
                lambda percent,message:self.report_progress(request.job_id,percent/100,message))
        except Cancelled:return {'status':'cancelled'}

    def _run_local_job(self, request: JobRequest, cancel_flag: CancelFlag) -> dict[str, Any]:
        job_id = request.job_id
        params = request.params

        video_path = params.get("video_path")
        if not video_path:
            return {"error": "video_path is required"}

        output_root = params.get("output_root")
        if not output_root:
            return {"error": "output_root is required"}

        project_id = params.get("project_id", 0)
        dance_setup = params.get("dance_setup")

        video_path = Path(video_path)
        output_root = Path(output_root)

        if not video_path.exists():
            logger.error("video file not found: %s", video_path)
            return {"error": f"video file not found: {video_path}"}

        logger.info("Starting dance highlight job %s: %s", job_id, video_path)

        def progress_cb(percent: int, message: str) -> None:
            if cancel_flag.is_set():
                return
            self.report_progress(job_id, percent / 100.0, message)

        self.report_progress(job_id, 0.10, "파이프라인 시작")

        meta = self._pipeline.run(
            project_root=output_root,
            input_video=video_path,
            project_id=project_id,
            progress_cb=progress_cb,
            dance_setup=dance_setup,
        )

        self.report_progress(job_id, 1.0, "완료")

        return {
            "status": "completed",
            "output_root": str(output_root),
            "meta": meta,
        }
