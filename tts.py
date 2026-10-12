"""TOEIC 예문 음성 생성기.

사용법: /usr/bin/python3 tts.py "<예문1>" "<예문2>" ...
각 예문을 audio/<sha1 앞 10자리>.mp3 로 저장하고 "id<TAB>경로<TAB>바이트" 를 출력한다.
하나라도 실패하면 0바이트 파일을 지우고 종료코드 1로 끝난다.
"""
import os
import sys

import certifi

# 프록시가 TLS를 재서명하므로 edge_tts import 전에 CA 번들을 교체한다(검증은 끄지 않는다).
CA = "/root/.ccr/ca-bundle.crt"
if os.path.exists(CA):
    certifi.where = lambda: CA

import asyncio
import hashlib

import edge_tts
from edge_tts import communicate, constants

VOICE = "en-US-AriaNeural"
RATE = "-15%"
# 2026-10 Microsoft가 speech.platform.bing.com(v1)을 403으로 막기 시작함(edge-tts #490).
# 새 호스트를 먼저 시도하고, 실패하면 기존 호스트로 폴백한다.
ENDPOINTS = [
    "wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1"
    f"?Ocp-Apim-Subscription-Key={constants.TRUSTED_CLIENT_TOKEN}",
    constants.WSS_URL,
]
ATTEMPTS = 3


def audio_id(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


async def synth(text, path):
    errors = []
    for attempt in range(ATTEMPTS):
        for url in ENDPOINTS:
            communicate.WSS_URL = url
            try:
                await edge_tts.Communicate(text, VOICE, rate=RATE).save(path)
            except Exception as e:  # noqa: BLE001 - 원인 보고용으로 모두 수집
                errors.append(f"[{attempt + 1}] {url.split('?')[0]}: {type(e).__name__}: {e}")
            if os.path.exists(path) and os.path.getsize(path) > 0:
                return None
            if os.path.exists(path):
                os.remove(path)
        await asyncio.sleep(2 ** attempt)
    return "\n".join(errors)


async def main(texts):
    os.makedirs("audio", exist_ok=True)
    failed = False
    for text in texts:
        i = audio_id(text)
        path = f"audio/{i}.mp3"
        err = await synth(text, path)
        if err:
            failed = True
            print(f"FAIL\t{i}\t{text}\n{err}", file=sys.stderr)
        else:
            print(f"{i}\t{path}\t{os.path.getsize(path)}")
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(asyncio.run(main(sys.argv[1:])))
