"""Create a client notebook using unchanged private inputs and the corrected runner."""
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[1]

def build():
    setup = (ROOT / "notebooks/render_kaggle_client_setup.py").read_text(encoding="utf-8")
    runner = (ROOT / "scripts/render_kaggle_bootstrap.py").read_text(encoding="utf-8")
    runner = runner.replace('WORK = Path("/kaggle/working/render-kaggle")', "WORK = CLIENT_WORK")
    runner = runner.rsplit('if __name__ == "__main__":', 1)[0]
    registrar = (ROOT / "scripts/render_kaggle_registration.py").read_text(encoding="utf-8")
    prefix = ("# Stable website configuration; never put keys in cells.\n"
              "import os\nBEAUTYCORE_PUBLIC_URL = 'https://beautycore-demo.onrender.com'\n"
              "os.environ['BEAUTYCORE_PUBLIC_URL'] = BEAUTYCORE_PUBLIC_URL\n"
              "(CLIENT_WORK / 'runtime_registration.py').write_text(" + repr(registrar) + ", encoding='utf-8')\n")
    cells = [
        ("markdown", "# BeautyCore scheduled demo starter\n\nUse the tested pinned Kaggle image, T4 GPU and Internet. Attach both private binary inputs and enable the three required Secrets. Run the three code cells in order, once per session. This notebook embeds the corrected CPU startup; the old private archives and model checks stay unchanged. See the client handover guide. Fresh Kaggle end-to-end rehearsal of this consolidated starter is still required.\n"),
        ("code", setup + "\nCLIENT_WORK = prepare()\n"),
        ("code", prefix + runner + "\nmain()\n"),
        ("code", "record = json.loads((CLIENT_WORK / 'demo-session.json').read_text())\nprint('Status:', record['status'])\nprint('Website:', BEAUTYCORE_PUBLIC_URL)\nprint('Connection:', record['status'])\nprint('Readiness is not proof of completed generation; rehearse all features.')\n"),
    ]
    notebook = {"nbformat":4,"nbformat_minor":5,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"}},
                "cells":[]}
    for index,(kind,source) in enumerate(cells):
        cell={"cell_type":kind,"id":"client-demo-"+str(index),"metadata":{},"source":source.splitlines(keepends=True)}
        if kind == "code":
            compile(source,"client-cell-"+str(index),"exec")
            cell.update(execution_count=None,outputs=[])
        notebook["cells"].append(cell)
    path = ROOT / "notebooks/render_kaggle_client_demo.ipynb"
    path.write_text(json.dumps(notebook,indent=1)+"\n",encoding="utf-8")
    return path

if __name__ == "__main__":
    print(build())
