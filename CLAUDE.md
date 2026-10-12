# toeic-tts 운영 지침 (스케줄 루틴용)

이 레포는 하루 3회 TOEIC 단어를 카톡으로 보내는 루틴이 사용한다. 루틴 프롬프트가 기본 절차이고, 이 문서는 그 절차를 보완한다.

## 음성 생성
- 루틴 프롬프트에 있는 인라인 파이썬 대신 `tts.py`를 우선 사용한다:
  `/usr/bin/python3 tts.py "<예문1>" "<예문2>"` → 출력의 id로 링크를 만든다.
  (새 호스트 api.msedgeservices.com → 기존 호스트 순으로 시도하고, 재시도와 0바이트 정리까지 한다.)
- `python3`가 pip 설치 대상과 다른 버전일 수 있다. `ModuleNotFoundError`가 나면 `/usr/bin/python3`(pip이 설치한 쪽)를 쓴다.
- TLS 검증을 끄는 우회(ssl=False, verify=False 등)는 어떤 경우에도 금지다.

## 실패 시: 바로 원인 분석 → 수정 → 재시도
어떤 단계든(설치, 음성 생성, push, Pages 반영, 카톡 발송) 실패하면 즉시 종료하지 말고 다음을 수행한다.
1. 오류 메시지 전문을 확보한다. HTTP 오류면 응답 헤더로 누가 거절했는지 구분한다
   (`x-msedge-ref` 등 서비스 헤더 → 원격 서비스, 그 외 → `curl -sS "$HTTPS_PROXY/__agentproxy/status"` 및 /root/.ccr/README.md로 프록시 확인).
2. 시계 오차(`date -u` vs 서버 Date 헤더), 패키지 버전(`pip index versions edge-tts`)을 확인한다.
3. edge-tts 문제면 https://github.com/rany2/edge-tts/issues 최신 이슈를 WebFetch로 읽고 보고된 수정/우회책을 찾는다.
4. 수정안을 작은 테스트(짧은 문장 1개, 레포 밖 경로)로 먼저 검증한다.
5. 검증된 수정은 `tts.py`(또는 해당 단계)에 반영하고, 아래 "장애 기록"에 한 줄 추가한 뒤, 원래 절차를 이어서 끝까지 수행한다.
6. 수정해서 완료했든 끝내 못 고쳤든, PushNotification으로 원인·조치·결과를 알린다.
   못 고친 경우 기존 규칙대로 카톡 미발송, 0바이트 파일 미커밋, history.csv 미수정.
- 안전 원칙은 그대로 지킨다. TLS 검증 해제, 테스트·검증 생략, 추측으로 링크 만들기, 사용자 확인 없이 범위 밖 변경(다른 레포, 설정 파일 대량 수정 등)은 하지 않는다.

## 장애 기록
- 2026-10-12: edge-tts WSServerHandshakeError 403. MS가 speech.platform.bing.com(v1) 차단을 지역별로 확대 중(edge-tts #490). WSS_URL을 api.msedgeservices.com 으로 교체해 해결 → tts.py 반영.
