# system-agents-plugins

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

[system-agents-template](https://github.com/southglory/system-agents-template)을 위한 공식 플러그인 모음.

각 플러그인은 이 레포의 하위 폴더로 독립적으로 배포된다. 사용자는 필요한 플러그인만 골라 설치한다.

## 🚀 한 줄 설치 (템플릿 설치기 경유)

이 레포를 직접 clone하지 말고, 템플릿의 `install.sh`를 써라. 이 스크립트가 여기 있는 `plugins.yaml` 인덱스를 읽어서 선택한 플러그인을 사용자 프로젝트에 복사한다.

```bash
curl -sSL https://raw.githubusercontent.com/southglory/system-agents-template/main/install.sh -o install.sh
bash install.sh
```

설치기가 "어떤 플러그인 설치할래?" 라고 물으면 `discord-huddle` (또는 다른 목록 플러그인) 선택.

## 플러그인 목록

| 폴더 | 설명 | 상태 |
|---|---|---|
| [`discord-huddle/`](discord-huddle/) | Discord 채팅 + 트래킹되는 회의록 파이프 | ✅ 배포 (`discord-huddle-v0.1.0`) |
| `unity-gamedev/` | Unity CLI 빌드 + GitHub Release 퍼블리시 | 🚧 준비 중 |

각 플러그인 폴더를 열면 자체 README에 설치 세부가 있다.

## 설치 모델

플러그인은 패키지 매니저(pip/npm)가 아니라 **파일 복사(`cp -r`)** 로 설치된다. 파일이 사용자 프로젝트 트리에 직접 병합되므로, 관리형 설치는 템플릿의 `install.sh` 책임이다.

```bash
# 1. 본 레포 clone (설치기가 자동 수행)
git clone https://github.com/southglory/system-agents-plugins.git

# 2. 원하는 플러그인을 프로젝트에 복사 (설치기가 자동 수행)
cp -r discord-huddle/bot/* /path/to/your-project/bot/
cp -r discord-huddle/skills/* /path/to/your-project/skills/

# 3. Claude Code 스킬 등록 (설치기가 자동 수행)
cp -r discord-huddle/skills/* ~/.claude/skills/

# 4. Python 의존 설치
cd /path/to/your-project
pip install -r discord-huddle/requirements.txt
```

수동 `cp -r` 흐름은 숙련자용 fallback이다. 일반적으로는 설치기 사용이 권장.

## 버전 태그 규약

플러그인별 독립 릴리즈. 태그 형식: `<플러그인명>-vX.Y.Z`.

- `discord-huddle-v0.1.0` — 첫 공개 릴리즈
- `unity-gamedev-v0.1.0` — (예정)

레포 전체 단일 버전은 쓰지 않는다. 템플릿 태그(`v2.x.x`)와 플러그인 태그는 결코 충돌하지 않음.

## 플러그인 조합

각 플러그인은 독립 동작을 전제로 설계되지만 조합이 유용한 경우가 있다. 조합 가능성은 [`CONTRIBUTING.md`](CONTRIBUTING.md)에 따라 각 플러그인 README의 "조합 가능한 플러그인" 섹션에 명시된다. 재사용 가능한 조합 레시피는 [`recipes/`](recipes/)에 위치.

## 호환성

- Claude Code (슬래시 스킬 시스템)
- system-agents-template v2.x 이상
- Python ≥ 3.10
- Windows / macOS / Linux

각 플러그인이 추가 요구사항을 명시할 수 있다 (예: discord-huddle은 Discord Bot Token 필요).

## 라이선스

[MIT](LICENSE) — system-agents-template과 동일.

## 기여

- 버그·피드백: GitHub Issues
- 새 플러그인 PR: [`CONTRIBUTING.md`](CONTRIBUTING.md) 규약 준수
