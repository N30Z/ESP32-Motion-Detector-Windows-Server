#!/usr/bin/env python3
"""
Face Recognition Pipeline - YuNet + SFace
==========================================
Lightweight face detection and recognition using OpenCV.

Models:
- YuNet: Fast face detector (ONNX)
- SFace: Embedding extractor (ONNX)

No PyTorch, no dlib, no heavy dependencies.
"""

import cv2
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)

class FaceRecognitionCV:
    """
    Face Recognition using OpenCV YuNet (detection) + SFace (embedding)
    """

    def __init__(self, config: dict):
        self.config = config
        self.enabled = config['face_recognition']['enabled']

        # Thresholds
        self.t_strict = config['face_recognition']['threshold_strict']
        self.t_loose = config['face_recognition']['threshold_loose']
        self.m_strict = config['face_recognition']['margin_strict']
        self.m_loose = config['face_recognition']['margin_loose']

        # Quality thresholds
        self.min_face_size = config['face_recognition']['min_face_size']
        self.min_quality_score = config['face_recognition']['min_quality_score']

        # Models
        models_dir = Path(__file__).parent / 'models'
        self.yunet_model = models_dir / 'face_detection_yunet_2023mar.onnx'
        self.sface_model = models_dir / 'face_recognition_sface_2021dec.onnx'

        self.detector = None
        self.recognizer = None

        if self.enabled:
            self._load_models()

    def _load_models(self):
        """Load YuNet and SFace models"""
        try:
            # Check model files exist
            if not self.yunet_model.exists():
                logger.error(f"YuNet model not found: {self.yunet_model}")
                logger.error("Run: python server/models/download_models.py")
                raise FileNotFoundError(f"YuNet model missing: {self.yunet_model}")

            if not self.sface_model.exists():
                logger.error(f"SFace model not found: {self.sface_model}")
                logger.error("Run: python server/models/download_models.py")
                raise FileNotFoundError(f"SFace model missing: {self.sface_model}")

            # Load YuNet (Face Detector)
            self.detector = cv2.FaceDetectorYN.create(
                model=str(self.yunet_model),
                config="",
                input_size=(320, 320),
                score_threshold=0.6,
                nms_threshold=0.3,
                top_k=5000
            )

            # Load SFace (Face Recognizer)
            self.recognizer = cv2.FaceRecognizerSF.create(
                model=str(self.sface_model),
                config=""
            )

            logger.info("✓ YuNet and SFace models loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            self.enabled = False
            raise

    def detect_faces(self, image_bytes: bytes) -> List[Dict]:
        """
        Detect faces in image

        Returns:
            List of face dicts with keys: bbox, landmarks, score
        """
        if not self.enabled:
            return []

        try:
            # Convert bytes to numpy array
            img_array = np.frombuffer(image_bytes, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if img is None:
                logger.error("Failed to decode image")
                return []

            # Set input size for detector
            h, w = img.shape[:2]
            self.detector.setInputSize((w, h))

            # Detect faces
            _, faces = self.detector.detect(img)

            if faces is None:
                return []

            # Parse detections
            face_list = []
            for face in faces:
                # face = [x, y, w, h, x_re, y_re, x_le, y_le, x_nt, y_nt, x_rcm, y_rcm, x_lcm, y_lcm, score]
                bbox = face[:4].astype(int).tolist()  # [x, y, w, h]
                landmarks = face[4:14].reshape(5, 2).astype(int).tolist()  # 5 landmarks
                score = float(face[14])

                # Calculate quality score (face size + detection confidence)
                face_area = bbox[2] * bbox[3]
                image_area = w * h
                size_ratio = face_area / image_area
                quality_score = score * (1 + size_ratio * 10)  # Boost for larger faces

                face_list.append({
                    'bbox': bbox,
                    'landmarks': landmarks,
                    'score': score,
                    'quality_score': quality_score
                })

            logger.debug(f"Detected {len(face_list)} faces")
            return face_list

        except Exception as e:
            logger.error(f"Face detection error: {e}")
            return []

    def extract_embedding(self, image_bytes: bytes, face: Dict) -> Optional[np.ndarray]:
        """
        Extract embedding for detected face

        Args:
            image_bytes: Original image as bytes
            face: Face dict from detect_faces()

        Returns:
            128-dim embedding vector or None
        """
        if not self.enabled:
            return None

        try:
            # Convert bytes to numpy array
            img_array = np.frombuffer(image_bytes, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if img is None:
                return None

            # Align face using landmarks (required for SFace)
            aligned_face = self.recognizer.alignCrop(img, face['landmarks'])

            # Extract feature (embedding)
            embedding = self.recognizer.feature(aligned_face)

            # embedding is 1x128, flatten to 128
            return embedding.flatten()

        except Exception as e:
            logger.error(f"Embedding extraction error: {e}")
            return None

    def crop_face(self, image_bytes: bytes, bbox: List[int], padding: float = 0.2) -> Optional[bytes]:
        """
        Crop face from image with padding

        Args:
            image_bytes: Original image
            bbox: [x, y, w, h]
            padding: Padding ratio (0.2 = 20% on each side)

        Returns:
            Cropped face as JPEG bytes
        """
        try:
            img_array = np.frombuffer(image_bytes, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if img is None:
                return None

            h, w = img.shape[:2]
            x, y, fw, fh = bbox

            # Add padding
            pad_w = int(fw * padding)
            pad_h = int(fh * padding)

            x1 = max(0, x - pad_w)
            y1 = max(0, y - pad_h)
            x2 = min(w, x + fw + pad_w)
            y2 = min(h, y + fh + pad_h)

            # Crop
            cropped = img[y1:y2, x1:x2]

            # Encode to JPEG
            _, buffer = cv2.imencode('.jpg', cropped, [cv2.IMWRITE_JPEG_QUALITY, 90])
            return buffer.tobytes()

        except Exception as e:
            logger.error(f"Face crop error: {e}")
            return None

    def match_embedding(
        self,
        query_embedding: np.ndarray,
        known_embeddings: List[Tuple[int, np.ndarray]]
    ) -> Dict:
        """
        Match query embedding against known embeddings

        Args:
            query_embedding: 128-dim vector
            known_embeddings: List of (person_id, embedding) tuples

        Returns:
            {
                'person_id': int or None,
                'distance': float,
                'margin': float,
                'status': 'GREEN' | 'YELLOW' | 'UNKNOWN',
                'confidence': float (0-100)
            }
        """
        if not known_embeddings:
            return {
                'person_id': None,
                'distance': 999.0,
                'margin': 0.0,
                'status': 'UNKNOWN',
                'confidence': 0.0
            }

        # Calculate distances to all known embeddings
        distances = []
        for person_id, emb in known_embeddings:
            # Cosine distance (SFace uses L2-normalized embeddings)
            dist = self.recognizer.match(
                query_embedding.reshape(1, -1),
                emb.reshape(1, -1),
                dis_type=cv2.FaceRecognizerSF_FR_COSINE
            )
            distances.append((person_id, float(dist)))

        # Sort by distance
        distances.sort(key=lambda x: x[1])

        # Best match
        best_person_id, d1 = distances[0]

        # Second best (for margin calculation)
        d2 = distances[1][1] if len(distances) > 1 else 999.0

        # Margin (how much better is best vs second best)
        margin = d2 - d1

        # Determine status based on distance and margin
        if d1 < self.t_strict and margin > self.m_strict:
            status = 'GREEN'  # Reliable match
        elif d1 < self.t_loose and margin > self.m_loose:
            status = 'YELLOW'  # Uncertain match
        else:
            status = 'UNKNOWN'  # No match

        # Calculate confidence (0-100)
        # Map distance to percentage (lower distance = higher confidence)
        if d1 < self.t_strict:
            base_conf = (self.t_loose - d1) / (self.t_loose - self.t_strict) * 100
        else:
            base_conf = max(0, (self.t_loose - d1) / self.t_loose * 50)

        # Adjust by margin (higher margin = more confident)
        margin_bonus = min(margin / self.m_strict * 20, 20)
        confidence = min(100, base_conf + margin_bonus)

        result = {
            'person_id': best_person_id if status != 'UNKNOWN' else None,
            'distance': d1,
            'margin': margin,
            'status': status,
            'confidence': round(confidence, 1)
        }

        logger.debug(f"Match result: {result}")
        return result

    def is_quality_acceptable(self, face: Dict) -> bool:
        """
        Check if face quality is acceptable for learning

        Args:
            face: Face dict from detect_faces()

        Returns:
            True if quality is acceptable
        """
        # Check face size
        bbox = face['bbox']
        face_area = bbox[2] * bbox[3]
        if face_area < self.min_face_size:
            logger.debug(f"Face too small: {face_area} < {self.min_face_size}")
            return False

        # Check quality score
        if face['quality_score'] < self.min_quality_score:
            logger.debug(f"Quality too low: {face['quality_score']} < {self.min_quality_score}")
            return False

        return True

    def process_image(
        self,
        image_bytes: bytes,
        known_embeddings: List[Tuple[int, np.ndarray]]
    ) -> List[Dict]:
        """
        Complete pipeline: detect faces, extract embeddings, match

        Args:
            image_bytes: Image as bytes
            known_embeddings: List of (person_id, embedding) from DB

        Returns:
            List of results:
            [
                {
                    'bbox': [x, y, w, h],
                    'landmarks': [[x, y], ...],
                    'embedding': np.ndarray,
                    'quality_score': float,
                    'match_result': {...},
                    'face_crop': bytes
                },
                ...
            ]
        """
        if not self.enabled:
            logger.warning("Face recognition is disabled")
            return []

        # Detect faces
        faces = self.detect_faces(image_bytes)

        if not faces:
            logger.debug("No faces detected")
            return []

        results = []

        for face in faces:
            # Extract embedding
            embedding = self.extract_embedding(image_bytes, face)

            if embedding is None:
                continue

            # Match against known embeddings
            match_result = self.match_embedding(embedding, known_embeddings)

            # Crop face
            face_crop = self.crop_face(image_bytes, face['bbox'])

            results.append({
                'bbox': face['bbox'],
                'landmarks': face['landmarks'],
                'embedding': embedding,
                'quality_score': face['quality_score'],
                'match_result': match_result,
                'face_crop': face_crop
            })

        logger.info(f"Processed {len(results)} faces")
        return results
