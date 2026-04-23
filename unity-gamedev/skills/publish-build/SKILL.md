---
name: publish-build
description: Unity 빌드 → zip → GitHub Release 공개. 프로젝트 루트 / 산출물 이름 / 씬 경로는 모두 CLI 플래그로 지정 (하드코딩 없음)
---

# Publish Build

`/publish-build` 명령이 수행하는 작업.

## 동작

1. Unity Editor(with `unity-cli` 연결됨)에 `BuildPlayerOptions`를 `unity-cli exec`로 밀어 넣어 빌드 실행.
2. 산출된 `Builds/{output-name}{확장자}`를 `dist/{output-name}_{tag}.zip`으로 압축.
3. `gh release create {tag}` 로 GitHub Release 생성 + zip 업로드 (기존 태그면 `gh release upload --clobber`로 폴백).
4. 릴리즈 URL을 얻어 stdout에 JSON 한 줄로 출력.

stderr은 사람이 읽는 진행 로그, stdout은 **기계 파싱용 JSON** 한 줄. 이 분리 덕분에 `/discord-huddle-post`에 파이프로 바로 연결 가능.

## 필수 도구

- `unity-cli` (`which unity-cli` 확인). `unity-cli v0.3+`.
- Unity Editor 실행 중 + `unity-cli status = ready` (Play 모드 아님).
- `gh` CLI, `repo` scope로 인증됨 (`gh auth status`).

## 실행

```bash
# 풀 빌드 + 릴리즈
python bot/publish_build.py \
  --tag v0.1.0-alpha \
  --scene Assets/Scenes/Main.unity \
  --output-name MyGame \
  --notes "MVP α"

# 다중 씬
python bot/publish_build.py --tag v0.1.1 \
  --scene Assets/Scenes/Boot.unity \
  --scene Assets/Scenes/Main.unity \
  --output-name MyGame

# 빌드 스킵 (기존 Builds/{output-name}.exe 재사용)
python bot/publish_build.py --tag v0.1.1-hotfix \
  --output-name MyGame --skip-build

# 프로젝트 루트 명시
python bot/publish_build.py --tag v0.2.0 \
  --project-root /path/to/UnityProject \
  --output-name MyGame \
  --scene Assets/Scenes/Main.unity
```

## CLI 플래그

| 플래그 | 필수 | 기본 | 설명 |
|---|---|---|---|
| `--tag TAG` | ✅ | — | 릴리즈 태그 (`v0.1.0` 등) |
| `--scene PATH` | `--skip-build` 미사용 시 | — | 프로젝트 루트 상대 씬 경로. 반복 가능 |
| `--output-name NAME` | | `Build` | `Builds/{NAME}.exe` + `dist/{NAME}_{tag}.zip` 이름 |
| `--target TARGET` | | `StandaloneWindows64` | Unity `BuildTarget` enum 값 |
| `--skip-build` | | off | Unity 빌드 생략, 기존 `Builds/{NAME}.*` 재사용 |
| `--title TITLE` | | `= TAG` | Release 제목 |
| `--notes NOTES` | | 빈 값 | 릴리즈 노트 (inline) |
| `--notes-file FILE` | | — | 파일에서 릴리즈 노트 읽기 (복수 줄 권장) |
| `--project-root PATH` | | 자동 탐색 | 지정 안 하면 `SYSTEM_AGENTS_PROJECT_ROOT` → cwd 상위의 `Assets/`+`ProjectSettings/` 순서로 찾음 |

## stdout JSON 스키마

```json
{
  "tag": "v0.1.0-alpha",
  "title": "MVP α",
  "url": "https://github.com/owner/repo/releases/tag/v0.1.0-alpha",
  "zip": "dist/MyGame_v0.1.0-alpha.zip",
  "output_name": "MyGame",
  "target": "StandaloneWindows64"
}
```

## 종료 코드

- `0` 성공
- `1` 빌드 / zip / gh 단계 실패
- `2` 입력 오류 (씬 누락, 노트 파일 없음, skip-build 모드인데 산출물 없음 등)
- `3` 프로젝트 루트 찾지 못함

## 플러그인 조합

Discord 채널에 릴리즈 공지까지 자동으로 하려면 [`discord-huddle`](../../discord-huddle/) 플러그인과 엮는다. 두 단계 파이프:

```bash
OUT=$(python bot/publish_build.py --tag v0.1.0 --skip-build --output-name MyGame)
URL=$(echo "$OUT" | jq -r .url)
TAG=$(echo "$OUT" | jq -r .tag)

python bot/discord_collab.py post --message "🚀 새 빌드: \`$TAG\`

**다운로드**: $URL

zip 다운로드 → 압축 풀기 → \`MyGame.exe\` 실행."
```

조합 recipe 전체: [`recipes/unity-build-to-discord/`](../../recipes/unity-build-to-discord/).

## 트러블슈팅

- `Unity project root undetermined` — CWD에 `Assets/` + `ProjectSettings/`가 없음. `--project-root` 명시하거나 해당 폴더에서 실행.
- `unity-cli exec failed: ...` — Unity Editor 미실행이거나 `unity-cli status`가 `ready`가 아님. Play 모드 종료 후 재시도.
- `Unity build did not succeed: result=Failed ...` — 씬에 컴파일 에러. `unity-cli console --type error` 로 에러 확인 후 해결.
- `gh release create failed: authentication required` — `gh auth refresh -h github.com -s repo`.
- `already exists` → 자동으로 `gh release upload --clobber` 폴백. 정상.
