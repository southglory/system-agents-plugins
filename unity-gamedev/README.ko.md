# unity-gamedev

![tests CI](https://github.com/southglory/system-agents-plugins/actions/workflows/tests.yml/badge.svg)
![unity-gamedev release](https://img.shields.io/github/v/tag/southglory/system-agents-plugins?filter=unity-gamedev-*&label=unity-gamedev)
![License](https://img.shields.io/github/license/southglory/system-agents-plugins)

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

Unity Editor + `unity-cli` + `gh` 조합을 **한 줄 릴리즈 파이프라인**으로 만들어주는 [system-agents-template](https://github.com/southglory/system-agents-template) 플러그인.

- **Build**: `unity-cli exec BuildPipeline.BuildPlayer(...)` — 씬·산출물·타겟을 호출자가 지정. **프로젝트명 하드코딩 없음**
- **Zip**: `Builds/{NAME}{확장자}` → `dist/{NAME}_{tag}.zip`
- **Release**: `gh release create {tag}` (재실행 시 `gh release upload --clobber`로 폴백)
- **공지 준비**: stdout의 JSON 한 줄은 `discord-huddle-post` 등 공지 스킬에 그대로 파이프 가능

## 🚀 한 줄 설치 (권장)

이 레포를 직접 clone하지 말고, 템플릿의 설치기를 써라:

롤링 (항상 `main` 최신):

```bash
curl -sSL https://raw.githubusercontent.com/southglory/system-agents-template/main/install.sh -o install.sh
bash install.sh
```

고정 릴리즈 (재현성 권장):

```bash
curl -sSL https://github.com/southglory/system-agents-template/releases/latest/download/install.sh -o install.sh
bash install.sh
```

플러그인 목록이 뜨면 `unity-gamedev` 선택. 설치 후 채워넣어야 할 비밀 없음 — 이미 있는 `gh` 로그인을 그대로 사용한다.

상세 설치: [`docs/SETUP.md`](docs/SETUP.md). 스모크 테스트: [`docs/SMOKE_TEST.md`](docs/SMOKE_TEST.md).

## 모든 것은 CLI 플래그

이 플러그인의 핵심은 **프로젝트명 하드코딩 없음**. 씬 경로, 산출물 이름, Unity 빌드 타겟, 프로젝트 루트 전부 호출자가 지정한다. 특정 게임에 맞춘 값이 박혀있지 않다:

```bash
python bot/publish_build.py \
  --tag v0.1.0 \
  --scene Assets/Scenes/Main.unity \
  --output-name MyGame \
  --target StandaloneWindows64
```

`--scene`은 반복 가능(다중 씬 빌드). `--skip-build`는 기존 `Builds/{NAME}.*` 재사용. 전체 플래그 표는 `skills/publish-build/SKILL.md` 참조.

## 출력: stdout JSON 한 줄

```json
{
  "tag": "v0.1.0",
  "title": "MVP α",
  "url": "https://github.com/owner/repo/releases/tag/v0.1.0",
  "zip": "dist/MyGame_v0.1.0.zip",
  "output_name": "MyGame",
  "target": "StandaloneWindows64"
}
```

stderr은 사람이 읽는 진행 로그. 이 분리 덕분에 후속 공지 단계를 스크립트로 엮기 쉽다.

## 다른 플러그인과의 조합

| 대상 | 효과 | 설정 | Recipe |
|---|---|---|---|
| [`discord-huddle`](../discord-huddle/) | Unity 빌드 → GitHub Release → 채널에 링크 자동 공지 | 두 플러그인 설치, `publish-build` JSON을 `discord-huddle-post`에 파이프 | [`recipes/unity-build-to-discord/`](../recipes/unity-build-to-discord/) |

## 슬래시 스킬

| 명령 | 역할 |
|---|---|
| `/publish-build` | Build + zip + Release를 한 번에 |

세부 contract는 [`skills/publish-build/SKILL.md`](skills/publish-build/SKILL.md).

## 요구사항

- **Python ≥ 3.10** (stdlib 전용 — `pip install` 필요 없음)
- Unity Editor 실행 중 + `unity-cli` 연결됨 (`unity-cli status = ready`)
- `unity-cli v0.3+` PATH에 있음
- `gh` CLI, `repo` scope 인증

## 이 플러그인이 하지 않는 것

- Unity 자체, `unity-cli`, `gh` 설치는 안 함
- git 태그는 밀지 않음 — GitHub **Release**만 만든다. git 태그가 필요하면 Release 전에 `git tag vX.Y.Z && git push --tags` 실행 (`--clobber` 폴백 덕분에 순서는 유연)
- 바이너리 서명/공증 안 함. 플랫폼별 도구 영역
- Steam/itch/앱스토어 업로드 안 함. 별도 플러그인으로 분리

## 라이선스

MIT — 레포 루트 [`LICENSE`](../LICENSE) 참조.

## 관련 문서

- [SETUP.md](docs/SETUP.md) — 설치 + 첫 릴리즈 순서
- [SMOKE_TEST.md](docs/SMOKE_TEST.md) — 7단계 수동 테스트 체크리스트
- 레포 루트 [README](../README.md) — 플러그인 생태계 개요
