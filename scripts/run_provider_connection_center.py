# 本文件核心功能：启动只监听本机回环地址的WJX数据接口接入中心页面。
# - 输入：Provider目录路径、无秘密档案路径、监听地址、端口和是否自动打开浏览器。
# - 处理：加载TASK_024C目录、初始化TASK_024D Windows凭据后端、组合TASK_024E服务与WSGI页面并启动标准库服务器。
# - 输出：本机浏览器可访问的接入中心；当前不注册任何真实券商测试器，因此不会连接外部网络或启用交易能力。
# - 常量依据：默认端口8765仅用于个人本机MVP；监听地址强制127.0.0.1，防止局域网暴露密钥输入页。
# - 为什么这样写：先用Python标准库提供可替换纵向样板，不引入新的Web框架依赖，也不让页面直接操作Windows凭据或领域对象。
"""Run the local-only WJX provider connection center."""

from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path
from wsgiref.simple_server import make_server


# 本段代码核心功能：定位项目仓库根目录。
# - 输入：当前脚本路径及父目录。
# - 处理：向上查找同时包含PROJECT_MEMORY.md和configs目录的首个位置。
# - 输出：仓库根Path；找不到时立即失败。
# - 为什么这样写：用户可从仓库根目录或scripts目录运行，不依赖当前PowerShell工作目录猜路径。
def locate_repository_root() -> Path:
    script = Path(__file__).resolve()
    for candidate in script.parents:
        if (candidate / "PROJECT_MEMORY.md").is_file() and (candidate / "configs").is_dir():
            return candidate
    raise RuntimeError("Cannot locate WJX repository root.")


# 本段代码核心功能：把仓库src目录加入当前脚本导入路径。
# - 输入：locate_repository_root返回的项目根目录。
# - 处理：仅在src尚未出现时插入sys.path首位，随后导入项目模块。
# - 输出：脚本无需依赖当前工作目录或editable install即可启动。
# - 为什么这样写：用户可能直接运行仓库脚本，显式源码路径比要求手工设置PYTHONPATH更可靠。
REPOSITORY_ROOT = locate_repository_root()
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from a_stock_quant.provider_connection_b2c import (  # noqa: E402
    JsonProviderConnectionProfileRepository,
    ProviderConnectionCenterService,
    ProviderConnectionCenterWSGIApp,
)
from a_stock_quant.provider_connection_center import load_connection_catalog  # noqa: E402
from a_stock_quant.windows_credential_store import WindowsCredentialStore  # noqa: E402


# 本段代码核心功能：定义本地接入中心命令行参数。
# - 输入：命令行argv。
# - 处理：提供目录、档案、地址、端口和打开浏览器选项；地址只允许127.0.0.1。
# - 输出：argparse Namespace。
# - 常量依据：Provider目录使用TASK_024C正式文件，档案默认由应用模块选择LocalAppData。
# - 为什么这样写：显式参数便于测试和后续桌面启动器复用，但安全地址不能由用户放宽到0.0.0.0。
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    root = REPOSITORY_ROOT
    parser = argparse.ArgumentParser(description="Run the local WJX provider connection center.")
    parser.add_argument(
        "--catalog",
        type=Path,
        default=root / "configs" / "providers" / "provider_connection_center_catalog_v1.json",
        help="Provider connection catalog path.",
    )
    parser.add_argument(
        "--profile-store",
        type=Path,
        default=None,
        help="Optional secret-free local profile JSON path.",
    )
    parser.add_argument("--host", default="127.0.0.1", choices=("127.0.0.1",))
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open-browser", action="store_true")
    return parser.parse_args(argv)


# 本段代码核心功能：初始化服务并持续处理本机HTTP请求。
# - 输入：已解析命令行参数。
# - 处理：加载目录、创建WindowsCredentialStore和档案仓储；测试器注册表保持为空；使用wsgiref启动。
# - 输出：直到用户Ctrl+C前持续提供页面，退出码0表示正常停止。
# - 为什么这样写：TASK_024E只交付统一页面与后端，真实Provider只读探针由TASK_024F通过testers端口注入。
def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not 1 <= args.port <= 65535:
        raise ValueError("port must be between 1 and 65535")
    definitions = load_connection_catalog(args.catalog)
    repository = JsonProviderConnectionProfileRepository(args.profile_store)
    service = ProviderConnectionCenterService(
        definitions=definitions,
        profile_repository=repository,
        credential_store=WindowsCredentialStore(),
        testers={},
    )
    application = ProviderConnectionCenterWSGIApp(service)
    url = f"http://{args.host}:{args.port}/provider-connections"
    print("WJX_PROVIDER_CONNECTION_CENTER_STARTED")
    print(f"url={url}")
    print("purpose=Configure provider connections safely; real SDK read-only tests begin in TASK_024F.")
    if args.open_browser:
        webbrowser.open(url)
    try:
        with make_server(args.host, args.port, application) as server:
            server.serve_forever()
    except KeyboardInterrupt:
        print("WJX_PROVIDER_CONNECTION_CENTER_STOPPED")
    return 0


# 本段代码核心功能：仅在脚本直接执行时启动服务器并返回可靠退出码。
# - 输入：Python模块运行标志。
# - 处理：调用main并交给SystemExit。
# - 输出：PowerShell或桌面启动器能够判断启动阶段是否失败。
# - 为什么这样写：测试导入本模块时不会意外启动本地服务器。
if __name__ == "__main__":
    sys.exit(main())
