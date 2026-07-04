"""Generate a complete FastAPI route inventory from the actual app.
This script must be run from the backend/ directory where the imports work.
"""
import sys
import os
import csv
from pathlib import Path

# Change to backend directory
os.chdir(str(Path(__file__).parent.parent / 'backend'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

# Direct import of create_app after adding src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend' / 'src'))

from app.factory import create_app

app = create_app()

rows = []
for route in app.routes:
    # Skip non-API routes
    if not hasattr(route, 'methods') or not hasattr(route, 'path'):
        continue
    if route.path in ['/', '/openapi.json', '/docs', '/redoc']:
        continue
    
    methods = route.methods - {'HEAD', 'OPTIONS'}
    for method in sorted(methods):
        endpoint = route.endpoint
        module = endpoint.__module__
        handler_name = endpoint.__name__
        
        # Get request/response model info
        hints = endpoint.__annotations__
        request_model = ''
        for name, hint in hints.items():
            if name != 'return':
                request_model = str(hint).split('.')[-1]
                break
        
        # Response model from route or return annotation
        response_model = getattr(route, 'response_model', None)
        response_model_name = response_model.__name__ if response_model else (
            str(hints.get('return', '')).split('.')[-1] if hints.get('return', '') else ''
        )
        
        rows.append([method, route.path, module, handler_name, request_model, response_model_name])

# Write CSV to project root
output_path = Path(__file__).parent.parent / 'FULL_ROUTE_INVENTORY.csv'
with open(output_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Method', 'Path', 'Router Module', 'Handler', 'RequestModel', 'ResponseModel'])
    writer.writerows(rows)

print(f"Total endpoints (excl. OpenAPI/docs): {len(rows)}")
print(f"Output: {output_path}")

# Summary by module
from collections import Counter
module_counts = Counter(r[2] for r in rows)
print("\nEndpoints per router:")
for module, count in sorted(module_counts.items()):
    print(f"  {module}: {count}")
print(f"\nTotal unique endpoints: {len(rows)}")