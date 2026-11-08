"""Prepare an isolated Runpod build context and private serving handoff."""
import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path
import shutil
from zipfile import ZipFile, ZIP_STORED

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_SHA = "b4a4e1c1482fd060d194f19f5570b6221131379e8214d18c064a713452ab08fd"
NAMES = ("capstone_train002_20260928_v1.bin", "beautycore_makeup_release_20261106.bin")
DIGESTS = ("f0d1fed52e00b6c5a1da2cade3731237675cdebbfc0b2cde3b2dbda99a4019ac",
           "0c657ae4d2b62e11bd8c5728321330d5416fbfd1d36354d8482ac548f1449357")


def digest(path):
    result = sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def helpers(notebook):
    raw = Path(notebook).read_bytes()
    if sha256(raw).hexdigest() != NOTEBOOK_SHA:
        raise ValueError("Final reviewed serving notebook changed")
    tree = ast.parse("".join(json.loads(raw)["cells"][1]["source"]))
    constants = {"BUNDLES", "STYLE_RELEASE_EXPECTED", "FILES", "OPTIMIZED_SOURCES"}
    selected = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef))
                or (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id in constants)]
    source = '"""Assembly definitions from the hash bound final Kaggle notebook. No startup calls."""\n'
    source += ast.unparse(ast.Module(body=selected, type_ignores=[])) + "\n"
    compile(source, "release_setup.py", "exec")
    return source


def build(destination, inputs, *, private_zip=True):
    destination, inputs = Path(destination).resolve(), Path(inputs).resolve()
    if destination.exists():
        raise ValueError("Choose a new output directory; old artifacts are preserved")
    sources = [inputs / name for name in NAMES]
    for path, expected in zip(sources, DIGESTS):
        if not path.is_file() or digest(path) != expected:
            raise ValueError("Private serving input missing or changed: " + path.name)
    source = helpers(ROOT / "notebooks/render_kaggle_makeup_corrective_demo.ipynb")
    context = destination / "build-context"
    context.mkdir(parents=True)
    for name in ("Dockerfile", ".dockerignore", "runtime.py", "profile.json"):
        shutil.copyfile(ROOT / "deploy/runpod" / name, context / name)
    (context / "release_setup.py").write_bytes(source.encode())
    shutil.copyfile(ROOT / "scripts/render_kaggle_registration.py", context / "registration.py")
    requirements = context / "requirements"
    requirements.mkdir()
    with ZipFile(sources[1]) as archive:
        for name in ("requirements.txt", "requirements-nails.txt", "requirements-demo-constraints.txt",
                     "requirements-nails-segmenter.txt"):
            (requirements / name).write_bytes(archive.read("backend/" + name))
    with ZipFile(sources[0]) as archive:
        (requirements / "gpu.txt").write_bytes(archive.read("scripts/unified_gate2_requirements.txt"))
    capabilities = json.loads((ROOT / "beautycore/lib/ai/style-release.json").read_text())
    namespace = {}
    exec(compile(source, "release_setup.py", "exec"), namespace)
    expected = namespace["STYLE_RELEASE_EXPECTED"]
    if any(capabilities[key] != expected[key] for key in ("release_id", "manifest_sha256")):
        raise ValueError("Render catalog and prepared release differ")
    catalogs = [row for row in capabilities["baseline_model_catalogs"] if len(row["hairstyle"]) == 18]
    if len(catalogs) != 1 or len(catalogs[0]["makeup"]) != 13 or len(capabilities["renderer_styles"]) != 6:
        raise ValueError("Complete serving catalog differs")
    manifest = {"schema": "beautycore-runpod-build-v1", "notebook_sha256": NOTEBOOK_SHA,
                "profile_id": "runpod-rtx3090-cu128-v1", "release_id": "styles-20261106-01",
                "catalog": {"model_styles": catalogs[0], "renderer_styles": capabilities["renderer_styles"]},
                "files": {p.relative_to(context).as_posix(): digest(p)
                          for p in sorted(context.rglob("*")) if p.is_file()},
                "private_inputs": {n: h for n, h in zip(NAMES, DIGESTS)},
                "linux_image_built": False, "real_gpu_validated": False, "deployed": False}
    (context / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(ROOT / "docs/guides/runpod-serving.md", destination / "START-HERE.md")
    target_inputs = destination / "inputs"
    target_inputs.mkdir()
    for path in sources:
        shutil.copyfile(path, target_inputs / path.name)
    if private_zip:
        archive_path = destination.with_suffix(".zip")
        if archive_path.exists():
            raise ValueError("Private ZIP already exists; choose a new output name")
        with ZipFile(archive_path, "x", compression=ZIP_STORED) as archive:
            for path in sorted(destination.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(destination).as_posix())
        with ZipFile(archive_path) as archive:
            if archive.testzip():
                raise ValueError("Private handoff ZIP failed integrity check")
        manifest["handoff_zip"] = {"path": str(archive_path), "sha256": digest(archive_path),
                                   "bytes": archive_path.stat().st_size}
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, default=ROOT / "client")
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.inputs), indent=2))
