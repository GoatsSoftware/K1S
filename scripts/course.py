"""Portable K1S build & deployment commands for Python gRPC microservices."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME_SERVICE = ROOT / "apps" / "game-service"
LEADERBOARD_SERVICE = ROOT / "apps" / "leaderboard-service"
API_GATEWAY = ROOT / "apps" / "api-gateway"
FRONTEND = ROOT / "apps" / "frontend"
WORKFLOWS = ROOT / ".github" / "workflows"
ARGO_WORKFLOWS = ROOT / ".argo" / "workflows"

ACTION_SHA = re.compile(r"^[0-9a-f]{40}$")
IMAGE_DIGEST = re.compile(r"@sha256:[0-9a-f]{64}(?:\s|$)")

# Service mappings
SERVICES = {
    "game-service": GAME_SERVICE,
    "leaderboard-service": LEADERBOARD_SERVICE,
    "api-gateway": API_GATEWAY,
}


def run(command: list[str], *, cwd: Path = ROOT) -> None:
    print(f"+ {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def get_venv_python() -> str:
    """Get Python interpreter from virtual environment or system."""
    venv_path = ROOT / ".venv"

    # Try venv first
    if venv_path.exists():
        if os.name == "nt":
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            python_exe = venv_path / "bin" / "python"

        if python_exe.exists():
            return str(python_exe)

    # Fall back to system Python
    return sys.executable


def setup_venv() -> None:
    """Create and configure Python virtual environment."""
    venv_path = ROOT / ".venv"

    if (venv_path / "bin" / "python").exists() or (venv_path / "Scripts" / "python.exe").exists():
        print(f"✓ Virtual environment already exists at {venv_path}")
    else:
        print("Creating virtual environment...")
        run([sys.executable, "-m", "venv", str(venv_path)])

    python_exe = get_venv_python()
    print(f"Using Python: {python_exe}")

    print("Upgrading pip...")
    run([python_exe, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])

    req_file = ROOT / "requirements.txt"
    if req_file.exists():
        print("Installing dependencies...")
        run([python_exe, "-m", "pip", "install", "-r", str(req_file)])

    req_dev_file = ROOT / "requirements-dev.txt"
    if req_dev_file.exists():
        print("Installing dev dependencies...")
        run([python_exe, "-m", "pip", "install", "-r", str(req_dev_file)])

    print(f"✓ Virtual environment ready at {venv_path}")
    print(f"  Activate with: source {venv_path}/bin/activate")


def test_python() -> None:
    """Run pytest on all services."""
    python_exe = get_venv_python()

    for service_name, service_path in SERVICES.items():
        tests_dir = service_path / "tests"
        if tests_dir.exists():
            print(f"\n📝 Testing {service_name}...")
            run([python_exe, "-m", "pytest", "-v", str(tests_dir)], cwd=service_path)


def test() -> None:
    """Run all tests."""
    test_python()


def lint_python() -> None:
    """Run Ruff checks on all Python code."""
    python_exe = get_venv_python()

    print("🔍 Checking with Ruff...")
    run([python_exe, "-m", "ruff", "check", "."], cwd=ROOT)

    print("📐 Verifying format...")
    run([python_exe, "-m", "ruff", "format", "--check", "."], cwd=ROOT)


def lint() -> None:
    """Run all linters."""
    lint_python()


def generate_grpc() -> None:
    """Generate Python gRPC stubs from .proto files."""
    python_exe = get_venv_python()

    proto_files = list(ROOT.glob("**/*.proto"))

    if not proto_files:
        print("⚠️  No .proto files found")
        return

    for proto_file in proto_files:
        print(f"\n📦 Generating gRPC stubs from {proto_file.relative_to(ROOT)}...")

        output_dir = proto_file.parent

        run(
            [
                python_exe,
                "-m",
                "grpc_tools.protoc",
                "-I",
                str(proto_file.parent),
                "--python_out",
                str(output_dir),
                "--grpc_python_out",
                str(output_dir),
                str(proto_file),
            ]
        )

    print("✓ gRPC code generation complete")


def build_local() -> None:
    """Build container images locally using buildx."""
    require_command("docker")

    for service_name, service_path in SERVICES.items():
        dockerfile = service_path / "Dockerfile"
        if not dockerfile.exists():
            print(f"⚠️  Skipping {service_name}: no Dockerfile found")
            continue

        print(f"\n🐳 Building {service_name} locally...")

        run(
            [
                "docker",
                "buildx",
                "build",
                "--platform",
                "linux/amd64",
                "--tag",
                f"k1s/{service_name}:dev",
                "--file",
                str(dockerfile),
                "--load",
                str(ROOT / "apps"),
            ]
        )


def build() -> None:
    """Build multi-platform images using buildx and push to registry."""
    require_command("docker")

    for service_name, service_path in SERVICES.items():
        dockerfile = service_path / "Dockerfile"
        if not dockerfile.exists():
            print(f"⚠️  Skipping {service_name}: no Dockerfile found")
            continue

        print(f"\n🐳 Building {service_name} (multi-platform)...")

        run(
            [
                "docker",
                "buildx",
                "build",
                "--platform",
                "linux/amd64,linux/arm64",
                "--tag",
                f"k1s/{service_name}:latest",
                "--file",
                str(dockerfile),
                "--push",
                str(ROOT / "apps"),
            ]
        )


def validate_workflows() -> None:
    """Validate Argo Workflow YAML syntax."""
    require_command("argo")

    workflows = sorted(ARGO_WORKFLOWS.glob("*.yaml")) + sorted(ARGO_WORKFLOWS.glob("*.yml"))

    if not workflows:
        print("⚠️  No Argo Workflow files found in .argo/workflows/")
        return

    for workflow_file in workflows:
        print(f"✓ Validating {workflow_file.name}...")
        run(["argo", "lint", str(workflow_file)])


def deploy() -> None:
    """Submit Argo Workflow to Kubernetes cluster."""
    require_command("kubectl")
    require_command("argo")

    workflows = sorted(ARGO_WORKFLOWS.glob("*.yaml")) + sorted(ARGO_WORKFLOWS.glob("*.yml"))

    if not workflows:
        raise RuntimeError("No Argo Workflow definitions found in .argo/workflows/")

    for workflow_file in workflows:
        print(f"\n🚀 Submitting {workflow_file.name}...")
        run(["argo", "submit", str(workflow_file), "--watch"])


def watch_workflows() -> None:
    """Watch Argo Workflow execution."""
    require_command("argo")
    run(["argo", "watch"])


def supply_chain_policy() -> None:
    """Validate supply chain security: pinned images and actions."""
    errors: list[str] = []

    # Check GitHub Actions
    workflows = sorted([*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")])

    for workflow in workflows:
        for line_number, line in enumerate(
            workflow.read_text(encoding="utf-8").splitlines(), start=1
        ):
            stripped = line.strip()
            if not stripped.startswith("uses:"):
                continue
            reference = stripped.removeprefix("uses:").split("#", maxsplit=1)[0].strip()
            if reference.startswith("./"):
                continue
            if "@" not in reference or not ACTION_SHA.fullmatch(reference.rsplit("@", 1)[1]):
                errors.append(
                    f"{workflow.relative_to(ROOT)}:{line_number}: action not pinned to a SHA"
                )

    # Check Dockerfiles for pinned base images
    for dockerfile in sorted((ROOT / "apps").glob("*/Dockerfile")):
        for line_number, line in enumerate(
            dockerfile.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if line.strip().upper().startswith("FROM ") and not IMAGE_DIGEST.search(line):
                errors.append(
                    f"{dockerfile.relative_to(ROOT)}:{line_number}: base image not pinned to digest"
                )

    if errors:
        raise RuntimeError("Supply-chain policy failed:\n" + "\n".join(errors))
    print("✓ Supply-chain policy validation passed")


def verify() -> None:
    """Run complete quality gate locally."""
    print("🔍 Starting verification pipeline...\n")

    generate_grpc()
    print("✓ gRPC generation passed\n")

    test()
    print("✓ Tests passed\n")

    lint()
    print("✓ Linting passed\n")

    supply_chain_policy()
    print("✓ Supply-chain policy passed\n")

    if shutil.which("docker"):
        build_local()
        print("✓ Local builds passed\n")
    else:
        print("⚠️  docker/buildx not found: skipping local build (built by Argo)\n")

    if shutil.which("argo"):
        validate_workflows()
        print("✓ Argo Workflow validation passed\n")
    else:
        print("⚠️  argo CLI not found: skipping workflow validation\n")

    print("✅ All verification steps passed!")


def require_command(command: str) -> None:
    if shutil.which(command) is None:
        raise RuntimeError(f"Required command not found: {command}")


def prerequisites() -> None:
    """Verify required tools."""
    checks = {
        "Python 3.8+": sys.executable,
        "pip": shutil.which("pip") or shutil.which("pip3"),
        "docker": shutil.which("docker"),
        "kubectl": shutil.which("kubectl"),
        "argo": shutil.which("argo"),
    }

    missing = False
    for name, location in checks.items():
        if location:
            print(f"✓ {name}: {location}")
        else:
            print(f"✗ {name}: NOT FOUND")
            missing = True

    if missing:
        raise RuntimeError("One or more prerequisites are missing")
    print("\n✅ All prerequisites satisfied")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "prerequisites",
            "setup-venv",
            "test",
            "lint",
            "generate-grpc",
            "build-local",
            "build",
            "validate-workflows",
            "deploy",
            "watch",
            "supply-chain-policy",
            "verify",
        ],
    )
    args = parser.parse_args()

    commands = {
        "prerequisites": prerequisites,
        "setup-venv": setup_venv,
        "test": test,
        "lint": lint,
        "generate-grpc": generate_grpc,
        "build-local": build_local,
        "build": build,
        "validate-workflows": validate_workflows,
        "deploy": deploy,
        "watch": watch_workflows,
        "supply-chain-policy": supply_chain_policy,
        "verify": verify,
    }

    try:
        commands[args.command]()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"❌ ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
