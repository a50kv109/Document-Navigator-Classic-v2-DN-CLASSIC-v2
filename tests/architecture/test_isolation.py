import os
import ast

def test_core_isolation():
    core_dir = "core/src"
    for root, _, files in os.walk(core_dir):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    try:
                        tree = ast.parse(f.read(), filename=path)
                    except SyntaxError:
                        continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            assert not alias.name.startswith("pipeline"), f"Isolation violation: {path} imports pipeline"
                            assert alias.name not in ["os", "sys", "zipfile"], f"Isolation violation: {path} imports I/O module {alias.name}"
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            assert not node.module.startswith("pipeline"), f"Isolation violation: {path} imports from pipeline"
                            assert node.module not in ["os", "sys", "zipfile"], f"Isolation violation: {path} imports from I/O module {node.module}"
