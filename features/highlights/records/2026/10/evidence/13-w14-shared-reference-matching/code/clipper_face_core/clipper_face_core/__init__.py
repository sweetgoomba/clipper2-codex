"""Plugin-neutral face detection and observation grouping API (schema v1)."""

from .grouping import FaceObservation, FaceGroup, FaceInterval, group_observations, rank_representatives
from .backend_types import ModelFiles, FaceDetection

__all__ = [
    "FaceObservation", "FaceGroup", "FaceInterval", "group_observations", "rank_representatives",
    "OpenCvFaceBackend", "ModelFiles", "FaceDetection",
]


def __getattr__(name):
    if name == "OpenCvFaceBackend":
        from .opencv_backend import OpenCvFaceBackend
        return OpenCvFaceBackend
    raise AttributeError(name)

from .contracts import (
    EmbeddingSpace, SourceEvidence, ReferenceSample, QueryEvidence, MatchPolicy,
    ReferenceGallery, ReferenceMatch, ConsensusResult, CandidateDistance,
)
from .gallery import build_gallery, GalleryBuildError

__all__ += [
    'EmbeddingSpace', 'SourceEvidence', 'ReferenceSample', 'QueryEvidence', 'MatchPolicy',
    'ReferenceGallery', 'ReferenceMatch', 'ConsensusResult', 'CandidateDistance',
    'build_gallery', 'GalleryBuildError',
]
from .matching import match_reference
__all__ += ['match_reference']
from .consensus import combine_reference_matches
__all__ += ['combine_reference_matches']
