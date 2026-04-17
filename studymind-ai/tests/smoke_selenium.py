import os
import socket
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path
import shutil

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app" / "main.py"
SELENIUM_CACHE = Path.home() / ".cache" / "selenium"
RUNTIME_DIR = ROOT / ".test-runtime"


def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_streamlit(port: int, timeout: float = 45.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(1)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.5)
    raise TimeoutError(f"Streamlit did not start on port {port} within {timeout} seconds.")


def _start_streamlit(port: int) -> subprocess.Popen[str]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    RUNTIME_DIR.mkdir(exist_ok=True)
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(APP_PATH),
            "--server.headless",
            "true",
            "--server.port",
            str(port),
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _latest_driver(exe_name: str) -> Path:
    candidates = sorted(SELENIUM_CACHE.rglob(exe_name))
    if not candidates:
        raise FileNotFoundError(f"Could not find {exe_name} under {SELENIUM_CACHE}")
    return candidates[-1]


def _make_chrome_driver(profile_dir: str) -> webdriver.Chrome:
    options = ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1440,1200")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-data-dir={profile_dir}")
    try:
        return webdriver.Chrome(options=options)
    except Exception:
        service = ChromeService(executable_path=str(_latest_driver("chromedriver.exe")))
        return webdriver.Chrome(service=service, options=options)


def _make_edge_driver(profile_dir: str) -> webdriver.Edge:
    options = EdgeOptions()
    options.use_chromium = True
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1440,1200")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.binary_location = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    try:
        return webdriver.Edge(options=options)
    except Exception:
        service = EdgeService(executable_path=str(_latest_driver("msedgedriver.exe")))
        return webdriver.Edge(service=service, options=options)


def _make_driver(profile_dir: str):
    try:
        return _make_chrome_driver(profile_dir)
    except Exception:
        return _make_edge_driver(profile_dir)


def _prepare_profile_dir() -> Path:
    profile_dir = RUNTIME_DIR / "browser-profile"
    if profile_dir.exists():
        shutil.rmtree(profile_dir, ignore_errors=True)
    profile_dir.mkdir(parents=True, exist_ok=True)
    return profile_dir


def main() -> int:
    port = _free_port()
    proc = _start_streamlit(port)
    driver = None

    try:
        _wait_for_streamlit(port)
        profile_dir = _prepare_profile_dir()
        driver = _make_driver(str(profile_dir))
        try:
            driver.get(f"http://127.0.0.1:{port}")

            wait = WebDriverWait(driver, 30)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            if "Uncaught app execution" in driver.page_source:
                raise AssertionError("Streamlit reported an uncaught app execution error.")

            try:
                wait.until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'study smarter')]",
                        )
                    )
                )
            except TimeoutException as exc:
                raise AssertionError("Auth landing page did not render expected hero text.") from exc

            print("Smoke test passed: auth landing page rendered.")
            return 0
        finally:
            driver.quit()
            shutil.rmtree(profile_dir, ignore_errors=True)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        if proc.stdout is not None:
            output = proc.stdout.read()
            if output:
                print("--- streamlit output ---")
                print(output)


if __name__ == "__main__":
    raise SystemExit(main())
