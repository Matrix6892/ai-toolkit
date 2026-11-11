"""Real consumer: one reader supplies both report heading and report detail."""
import json
from artifact_bundle import open_package

def render(reader):
    summary = json.loads(reader.read('summary.json'))
    detail = reader.read('detail.txt').decode('utf-8')
    return summary['title'] + '\n' + detail

def current_report(root):
    reader = open_package(root)
    return None if reader is None else render(reader)
