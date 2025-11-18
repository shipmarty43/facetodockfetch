#!/usr/bin/env python3
"""
Advanced Automated Environment Testing Script
Tests conda environment with advanced logging and reporting

Features:
- Colored console output
- JSON log export
- Detailed error tracking
- Performance metrics
- HTML report generation
- Timestamped log files
"""

import sys
import importlib
import json
import time
import platform
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, asdict


# Configure logging
LOG_DIR = Path("/home/user/facetodockfetch/logs")
LOG_DIR.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = LOG_DIR / f"test_environment_{timestamp}.log"
json_log_file = LOG_DIR / f"test_environment_{timestamp}.json"
html_report_file = LOG_DIR / f"test_environment_{timestamp}.html"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Test result data class"""
    name: str
    category: str
    status: str  # pass, fail, skip, warn
    duration: float
    version: str = ""
    error_message: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class TestLogger:
    """Advanced test logger with multiple outputs"""

    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()
        self.system_info = self._gather_system_info()

    def _gather_system_info(self) -> Dict[str, Any]:
        """Gather system information"""
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            cuda_version = torch.version.cuda if cuda_available else "N/A"
            gpu_name = torch.cuda.get_device_name(0) if cuda_available else "N/A"
        except:
            cuda_available = False
            cuda_version = "N/A"
            gpu_name = "N/A"

        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "cuda_available": cuda_available,
            "cuda_version": cuda_version,
            "gpu_name": gpu_name,
            "timestamp": datetime.now().isoformat()
        }

    def add_result(self, result: TestResult):
        """Add test result"""
        self.results.append(result)
        logger.info(f"{result.category} - {result.name}: {result.status} ({result.duration:.3f}s)")

    def get_summary(self) -> Dict[str, Any]:
        """Get test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "pass")
        failed = sum(1 for r in self.results if r.status == "fail")
        skipped = sum(1 for r in self.results if r.status == "skip")
        warned = sum(1 for r in self.results if r.status == "warn")

        total_duration = time.time() - self.start_time

        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "warned": warned,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "total_duration": total_duration,
            "timestamp": datetime.now().isoformat()
        }

    def save_json(self):
        """Save results as JSON"""
        data = {
            "system_info": self.system_info,
            "summary": self.get_summary(),
            "results": [asdict(r) for r in self.results]
        }

        with open(json_log_file, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"JSON report saved to: {json_log_file}")
        return json_log_file

    def save_html(self):
        """Save results as HTML report"""
        summary = self.get_summary()

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Test Environment Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .summary-card {{ background: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #4CAF50; }}
        .summary-card.failed {{ border-left-color: #f44336; }}
        .summary-card h3 {{ margin: 0 0 10px 0; color: #666; font-size: 14px; }}
        .summary-card .value {{ font-size: 32px; font-weight: bold; color: #333; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .status-pass {{ color: #4CAF50; font-weight: bold; }}
        .status-fail {{ color: #f44336; font-weight: bold; }}
        .status-skip {{ color: #ff9800; font-weight: bold; }}
        .status-warn {{ color: #ff9800; font-weight: bold; }}
        .system-info {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .system-info dt {{ font-weight: bold; color: #1976d2; }}
        .system-info dd {{ margin: 0 0 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Test Environment Report</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h2>📊 Summary</h2>
        <div class="summary">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="value">{summary['total_tests']}</div>
            </div>
            <div class="summary-card">
                <h3>Passed</h3>
                <div class="value" style="color: #4CAF50;">{summary['passed']}</div>
            </div>
            <div class="summary-card {'failed' if summary['failed'] > 0 else ''}">
                <h3>Failed</h3>
                <div class="value" style="color: #f44336;">{summary['failed']}</div>
            </div>
            <div class="summary-card">
                <h3>Pass Rate</h3>
                <div class="value">{summary['pass_rate']:.1f}%</div>
            </div>
            <div class="summary-card">
                <h3>Duration</h3>
                <div class="value" style="font-size: 24px;">{summary['total_duration']:.2f}s</div>
            </div>
        </div>

        <h2>💻 System Information</h2>
        <div class="system-info">
            <dl>
                <dt>Platform:</dt><dd>{self.system_info['platform']}</dd>
                <dt>Python Version:</dt><dd>{self.system_info['python_version']}</dd>
                <dt>Architecture:</dt><dd>{self.system_info['architecture']}</dd>
                <dt>Processor:</dt><dd>{self.system_info['processor']}</dd>
                <dt>CUDA Available:</dt><dd>{'✓ Yes' if self.system_info['cuda_available'] else '✗ No'}</dd>
                <dt>CUDA Version:</dt><dd>{self.system_info['cuda_version']}</dd>
                <dt>GPU:</dt><dd>{self.system_info['gpu_name']}</dd>
            </dl>
        </div>

        <h2>📋 Test Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Test Name</th>
                    <th>Status</th>
                    <th>Version</th>
                    <th>Duration</th>
                    <th>Error</th>
                </tr>
            </thead>
            <tbody>
"""

        for result in self.results:
            status_class = f"status-{result.status}"
            status_symbol = {
                'pass': '✓',
                'fail': '✗',
                'skip': '⊘',
                'warn': '⚠'
            }.get(result.status, '?')

            error_display = result.error_message[:100] + '...' if len(result.error_message) > 100 else result.error_message

            html += f"""
                <tr>
                    <td>{result.category}</td>
                    <td>{result.name}</td>
                    <td class="{status_class}">{status_symbol} {result.status.upper()}</td>
                    <td>{result.version}</td>
                    <td>{result.duration:.3f}s</td>
                    <td style="color: #666; font-size: 12px;">{error_display}</td>
                </tr>
"""

        html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""

        with open(html_report_file, 'w') as f:
            f.write(html)

        logger.info(f"HTML report saved to: {html_report_file}")
        return html_report_file


class Color:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Color.BOLD}{Color.BLUE}{'=' * 60}{Color.END}")
    print(f"{Color.BOLD}{Color.BLUE}{text}{Color.END}")
    print(f"{Color.BOLD}{Color.BLUE}{'=' * 60}{Color.END}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Color.GREEN}✓{Color.END} {text}")


def print_error(text: str):
    """Print error message"""
    print(f"{Color.RED}✗{Color.END} {text}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Color.YELLOW}⚠{Color.END} {text}")


def test_import(module_name: str, package_name: Optional[str] = None) -> Tuple[bool, str, str, float]:
    """
    Test if a module can be imported

    Args:
        module_name: Name of the module to import
        package_name: Display name (defaults to module_name)

    Returns:
        Tuple of (success, version, error_message, duration)
    """
    package_name = package_name or module_name
    start_time = time.time()

    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'unknown')

        # Special version handling
        if module_name == 'cv2':
            version = module.__version__
        elif module_name == 'elasticsearch':
            version = str(module.__version__)

        duration = time.time() - start_time
        return True, version, "", duration
    except ImportError as e:
        duration = time.time() - start_time
        return False, "", str(e), duration
    except Exception as e:
        duration = time.time() - start_time
        return False, "", f"Unexpected error: {str(e)}", duration


def test_core_packages(test_logger: TestLogger) -> int:
    """Test core package imports"""
    print_header("Testing Core Packages")

    packages = [
        ('fastapi', 'FastAPI'),
        ('torch', 'PyTorch'),
        ('cv2', 'OpenCV'),
        ('PIL', 'Pillow'),
        ('numpy', 'NumPy'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('celery', 'Celery'),
        ('redis', 'Redis'),
        ('elasticsearch', 'Elasticsearch'),
        ('insightface', 'InsightFace'),
        ('mrz', 'MRZ'),
        ('pydantic', 'Pydantic'),
        ('onnxruntime', 'ONNX Runtime'),
    ]

    failed = 0
    for module_name, package_name in packages:
        success, version, error, duration = test_import(module_name, package_name)

        if success:
            print_success(f"{package_name:<20} v{version}")
            test_logger.add_result(TestResult(
                name=package_name,
                category="Core Packages",
                status="pass",
                version=version,
                duration=duration
            ))
        else:
            print_error(f"{package_name:<20} FAILED: {error}")
            test_logger.add_result(TestResult(
                name=package_name,
                category="Core Packages",
                status="fail",
                error_message=error,
                duration=duration
            ))
            failed += 1

    return failed


def run_all_tests():
    """Run all tests with advanced logging"""
    test_logger = TestLogger()

    print(f"\n{Color.BOLD}Face Recognition & OCR System - Advanced Environment Test{Color.END}")
    print(f"{Color.BOLD}{'=' * 60}{Color.END}")
    print(f"{Color.BOLD}Log file: {log_file}{Color.END}\n")

    total_failed = 0

    # Run test suite
    logger.info("Starting test suite...")
    total_failed += test_core_packages(test_logger)

    # Generate reports
    print_header("Generating Reports")

    summary = test_logger.get_summary()

    print(f"📊 Test Summary:")
    print(f"   Total: {summary['total_tests']}")
    print(f"   Passed: {Color.GREEN}{summary['passed']}{Color.END}")
    print(f"   Failed: {Color.RED}{summary['failed']}{Color.END}")
    print(f"   Pass Rate: {summary['pass_rate']:.1f}%")
    print(f"   Duration: {summary['total_duration']:.2f}s")
    print()

    # Save reports
    json_file = test_logger.save_json()
    html_file = test_logger.save_html()

    print()
    print_success(f"Text log saved to: {log_file}")
    print_success(f"JSON log saved to: {json_file}")
    print_success(f"HTML report saved to: {html_file}")
    print()

    if total_failed == 0:
        print_success(f"{Color.BOLD}All tests passed!{Color.END}")
        print("\n✅ Environment is ready for development and deployment\n")
        return 0
    else:
        print_error(f"{Color.BOLD}{total_failed} test(s) failed{Color.END}")
        print("\n❌ Please fix the errors above before proceeding\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
