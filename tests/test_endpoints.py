"""
Test all API endpoints.
"""

import asyncio
import httpx
import json
from uuid import UUID


BASE_URL = "http://localhost:8000"


async def test_all_endpoints():
    """Test all API endpoints in sequence."""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("=" * 70)
        print("TESTING ALL API ENDPOINTS")
        print("=" * 70)
        
        # 1. Health checks
        print("\n1. HEALTH CHECKS")
        print("-" * 70)
        
        response = await client.get(f"{BASE_URL}/")
        print(f"GET / : {response.status_code}")
        print(f"Response: {response.json()}\n")
        
        response = await client.get(f"{BASE_URL}/health")
        print(f"GET /health : {response.status_code}")
        print(f"Response: {response.json()}\n")
        
        response = await client.get(f"{BASE_URL}/api/v1/health")
        print(f"GET /api/v1/health : {response.status_code}")
        print(f"Response: {response.json()}\n")
        
        # 2. Create workflow
        print("\n2. CREATE WORKFLOW")
        print("-" * 70)
        
        workflow_data = {
            "name": "Test Code Review",
            "description": "Test workflow for API testing",
            "graph_definition": {
                "nodes": [
                    {
                        "name": "extract_functions",
                        "type": "normal",
                        "tool_name": "extract_functions"
                    },
                    {
                        "name": "improvement_loop",
                        "type": "loop",
                        "nodes": ["check_complexity", "detect_issues", "calculate_quality", 
                                 "suggest_improvements", "apply_suggestions"],
                        "loop_condition": {
                            "field": "quality_score",
                            "operator": ">=",
                            "value": 8
                        },
                        "max_iterations": 15,
                        "on_max_reached": "fail"
                    },
                    {"name": "check_complexity", "type": "normal", "tool_name": "check_complexity"},
                    {"name": "detect_issues", "type": "normal", "tool_name": "detect_issues"},
                    {"name": "calculate_quality", "type": "normal", "tool_name": "calculate_quality"},
                    {"name": "suggest_improvements", "type": "normal", "tool_name": "suggest_improvements"},
                    {"name": "apply_suggestions", "type": "normal", "tool_name": "apply_suggestions"}
                ],
                "edges": [
                    {"from_node": "extract_functions", "to_node": "improvement_loop"}
                ],
                "initial_state_schema": {
                    "code": "str"
                }
            }
        }
        
        response = await client.post(f"{BASE_URL}/api/v1/graph/create", json=workflow_data)
        print(f"POST /api/v1/graph/create : {response.status_code}")
        create_response = response.json()
        print(f"Response: {json.dumps(create_response, indent=2)}\n")
        
        workflow_id = create_response["workflow_id"]
        
        # 3. List workflows
        print("\n3. LIST WORKFLOWS")
        print("-" * 70)
        
        response = await client.get(f"{BASE_URL}/api/v1/graph/list")
        print(f"GET /api/v1/graph/list : {response.status_code}")
        workflows = response.json()
        print(f"Found {len(workflows)} workflow(s)")
        print(f"Response: {json.dumps(workflows, indent=2)}\n")
        
        # 4. Run workflow
        print("\n4. RUN WORKFLOW")
        print("-" * 70)
        
        run_data = {
            "workflow_id": workflow_id,
            "initial_state": {
                "code": """def greet(name: str) -> str:
    \"\"\"Greet a person.\"\"\"
    return f"Hello, {name}!"
""",
                "functions": [],
                "complexity_scores": {},
                "issues": [],
                "quality_score": 0,
                "suggestions": [],
                "improvements_applied": 0
            }
        }
        
        response = await client.post(f"{BASE_URL}/api/v1/graph/run", json=run_data)
        print(f"POST /api/v1/graph/run : {response.status_code}")
        run_response = response.json()
        print(f"Response: {json.dumps(run_response, indent=2)}\n")
        
        run_id = run_response["run_id"]
        
        # 5. Poll for completion
        print("\n5. CHECK WORKFLOW STATUS (Polling)")
        print("-" * 70)
        
        max_polls = 10
        for poll in range(1, max_polls + 1):
            await asyncio.sleep(1)
            
            response = await client.get(f"{BASE_URL}/api/v1/graph/state/{run_id}")
            print(f"GET /api/v1/graph/state/{run_id} : {response.status_code}")
            
            state_response = response.json()
            status = state_response["status"]
            
            print(f"Poll {poll}: status={status}, iteration={state_response['iteration_count']}")
            
            if status in ["completed", "failed"]:
                print(f"\nFinal Response:")
                print(f"  Status: {status}")
                print(f"  Quality Score: {state_response['state'].get('quality_score', 'N/A')}")
                print(f"  Functions: {len(state_response['state'].get('functions', []))}")
                print(f"  Issues: {len(state_response['state'].get('issues', []))}")
                print(f"  Logs: {len(state_response['logs'])} entries")
                if state_response.get('error_message'):
                    print(f"  Error: {state_response['error_message']}")
                break
        
        # 6. List runs
        print("\n\n6. LIST WORKFLOW RUNS")
        print("-" * 70)
        
        response = await client.get(f"{BASE_URL}/api/v1/graph/runs")
        print(f"GET /api/v1/graph/runs : {response.status_code}")
        runs = response.json()
        print(f"Found {len(runs)} run(s)")
        print(f"Response: {json.dumps(runs[:2], indent=2)}\n")  # Show first 2
        
        # 7. Filter runs by workflow
        print("\n7. FILTER RUNS BY WORKFLOW")
        print("-" * 70)
        
        response = await client.get(f"{BASE_URL}/api/v1/graph/runs?workflow_id={workflow_id}")
        print(f"GET /api/v1/graph/runs?workflow_id={workflow_id} : {response.status_code}")
        filtered_runs = response.json()
        print(f"Found {len(filtered_runs)} run(s) for this workflow\n")
        
        # 8. Filter runs by status
        print("\n8. FILTER RUNS BY STATUS")
        print("-" * 70)
        
        response = await client.get(f"{BASE_URL}/api/v1/graph/runs?status=completed")
        print(f"GET /api/v1/graph/runs?status=completed : {response.status_code}")
        completed_runs = response.json()
        print(f"Found {len(completed_runs)} completed run(s)\n")
        
        print("=" * 70)
        print("ALL ENDPOINT TESTS COMPLETED ✅")
        print("=" * 70)


if __name__ == "__main__":
    print("\n⚠️  Make sure the server is running: uvicorn app.main:app --reload")
    print("Press Enter to start testing...")
    input()
    
    asyncio.run(test_all_endpoints())
