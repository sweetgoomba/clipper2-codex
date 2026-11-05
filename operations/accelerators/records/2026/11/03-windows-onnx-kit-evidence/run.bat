@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
rem 파이썬·패키지는 전부 이 폴더 안(.python, .uvcache)에만 받는다 — 시험 뒤 폴더째 지우면 흔적이 없다.
set "UV_PYTHON_INSTALL_DIR=%~dp0.python"
set "UV_CACHE_DIR=%~dp0.uvcache"
set "PYTHONIOENCODING=utf-8"
echo Clipper GPU 시험을 시작합니다. 15~30분 걸릴 수 있어요. 창을 닫지 마세요.
echo.
echo [1/3] DirectML 판 시험
"%~dp0uv.exe" run --no-project --python 3.11 --with onnxruntime-directml==1.24.4 --with numpy python run_kit.py --label directml
echo.
echo [2/3] Windows ML 판 시험
"%~dp0uv.exe" run --no-project --python 3.11 --with onnxruntime-windowsml==1.30.0.202609102321 --with numpy python run_kit.py --label windowsml
echo.
echo [3/3] Windows ML 제조사 실행기 시험 (Windows 11 24H2 이상 + Windows App SDK 런타임 필요, NVIDIA는 RTX 30 이상, 실패해도 괜찮아요)
rem wasdk 2.3.0은 onnxruntime-windowsml 1.25.2를 고정해서 데려온다 — 여기서 ORT 버전을 따로 박지 않는다.
"%~dp0uv.exe" run --no-project --python 3.11 --with "wasdk-Microsoft.Windows.AI.MachineLearning[all]==2.3.0" --with wasdk-Microsoft.Windows.ApplicationModel.DynamicDependency.Bootstrap==2.3.0 --with numpy python run_kit.py --label windowsml-vendor --winml-catalog
echo.
echo 끝났어요. 열리는 results 폴더를 통째로 보내 주세요.
if exist "%~dp0results" explorer "%~dp0results"
pause
