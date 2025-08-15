# /var/www/tiktok-automation/backend/services/transcription_service.py

import os
import time
import logging
from typing import List, Dict, Optional
import requests

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Serviço simples de transcrição usando AssemblyAI.

    - Requer variável de ambiente ASSEMBLYAI_KEY.
    - Fluxo: upload do arquivo -> criar transcript -> poll até concluir -> obter palavras -> agrupar em segmentos.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ASSEMBLYAI_KEY")
        self.base_url = "https://api.assemblyai.com/v2"
        if not self.api_key:
            logger.warning("⚠️ ASSEMBLYAI_KEY não configurada; TranscriptionService ficará inativo")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def transcribe(self, audio_path: str, max_segment_duration: float = 6.0, max_words_per_segment: int = 14) -> Optional[List[Dict]]:
        """Transcreve áudio e retorna lista de segmentos {start, end, text} em segundos.

        Implementa uma agregação simples por palavras com limites de tempo e quantidade de palavras.
        """
        if not self.is_available():
            return None
        try:
            # 1) Upload
            upload_url = self._upload_file(audio_path)
            if not upload_url:
                return None

            # 2) Criar transcript
            transcript_id = self._create_transcript(upload_url)
            if not transcript_id:
                return None

            # 3) Poll até concluir
            result = self._wait_transcript(transcript_id)
            if not result or result.get('status') != 'completed':
                logger.error(f"❌ Transcrição não concluída: {result}")
                return None

            words = result.get('words') or []
            if not words:
                logger.warning("⚠️ Nenhuma palavra retornada pela transcrição")
                return None

            # 4) Agrupar palavras em segmentos
            segments: List[Dict] = []
            cur_text: List[str] = []
            cur_start: Optional[float] = None
            cur_end: Optional[float] = None

            def flush_segment():
                nonlocal cur_text, cur_start, cur_end
                if cur_text and cur_start is not None and cur_end is not None:
                    segments.append({
                        'start': cur_start / 1000.0,
                        'end': cur_end / 1000.0,
                        'text': ' '.join(cur_text).strip()
                    })
                cur_text = []
                cur_start = None
                cur_end = None

            punctuations = {'.', ',', '!', '?', ';', ':'}
            for w in words:
                w_text = (w.get('text') or '').strip()
                w_start = w.get('start')
                w_end = w.get('end')
                if w_text == '':
                    continue
                if cur_start is None:
                    cur_start = w_start
                cur_end = w_end
                cur_text.append(w_text)

                # Critérios de quebra: pontuação, tamanho, duração
                duration_ms = (cur_end - cur_start) if (cur_end and cur_start) else 0
                if (w_text[-1:] in punctuations) or (len(cur_text) >= max_words_per_segment) or (duration_ms / 1000.0 >= max_segment_duration):
                    flush_segment()

            # Flush final
            flush_segment()

            logger.info(f"✅ Transcrição concluída com {len(segments)} segmentos")
            return segments
        except Exception as e:
            logger.error(f"❌ Erro na transcrição: {e}")
            return None

    # ---- Métodos auxiliares AssemblyAI ----
    def _upload_file(self, file_path: str) -> Optional[str]:
        try:
            headers = {"authorization": self.api_key}
            with open(file_path, 'rb') as f:
                resp = requests.post(f"{self.base_url}/upload", headers=headers, data=f)
            if resp.status_code == 200:
                url = resp.json().get('upload_url')
                return url
            logger.error(f"❌ Falha no upload AssemblyAI: {resp.status_code} {resp.text}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro no upload AssemblyAI: {e}")
            return None

    def _create_transcript(self, audio_url: str) -> Optional[str]:
        try:
            headers = {"authorization": self.api_key, "content-type": "application/json"}
            payload = {
                "audio_url": audio_url,
                "language_detection": True,
                "punctuate": True,
                "format_text": True,
                "disfluencies": False,
                "word_boost": [],
                "boost_param": "high"
            }
            resp = requests.post(f"{self.base_url}/transcript", headers=headers, json=payload)
            if resp.status_code in (200, 201):
                return resp.json().get('id')
            logger.error(f"❌ Falha ao criar transcript: {resp.status_code} {resp.text}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao criar transcript: {e}")
            return None

    def _wait_transcript(self, transcript_id: str, timeout_s: int = 600, poll_interval: float = 5.0) -> Optional[Dict]:
        try:
            headers = {"authorization": self.api_key}
            url = f"{self.base_url}/transcript/{transcript_id}"
            start = time.time()
            while time.time() - start < timeout_s:
                resp = requests.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get('status')
                    if status in ('completed', 'error'):
                        return data
                time.sleep(poll_interval)
            logger.error("❌ Timeout aguardando AssemblyAI transcript")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao aguardar transcript: {e}")
            return None
