"""
API Integration Test.

Tests the complete workflow engine via HTTP API.
"""

import asyncio
import httpx
from typing import Any


BASE_URL = "http://localhost:8000/api/v1"


async def test_complete_workflow():
    """Test complete workflow creation and execution."""
    
    print("\n" + "=" * 60)
    print("API Integration Test")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Health check
        print("\n1. Testing health check...")
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        print(f"   ✓ Health check: {response.json()}")
        
        # Test 2: Create workflow
        print("\n2. Creating workflow...")
        workflow_data = {
            "name": "Simple Counter Workflow",
            "description": "Test workflow with loop",
            "graph_definition": {
                "nodes": [
                    {
                        "name": "start",
                        "type": "normal",
                        "tool_name": "increment"
                    },
                    {
                        "name": "improvement_loop",
                        "type": "loop",
                        "nodes": ["increment", "quality_check"],
                        "loop_condition": {
                            "field": "quality_score",
                            "operator": ">=",
                            "value": 8
                        },
                        "max_iterations": 15,
                        "on_max_reached": "fail"
                    }
                ],
                "edges": [
                    {"from_node": "start", "to_node": "improvement_loop"}
                ],
                "initial_state_schema": {
                    "count": "int",
                    "quality_score": "int"
                }
            }
        }
        
        response = await client.post(f"{BASE_URL}/graph/create", json=workflow_data)
        assert response.status_code == 200
        workflow_id = response.json()["workflow_id"]
        print(f"   ✓ Workflow created: {workflow_id}")
        
        # Test 3: List workflows
        print("\n3. Listing workflows...")
        response = await client.get(f"{BASE_URL}/graph/list")
        assert response.status_code == 200
        workflows = response.json()
        print(f"   ✓ Found {len(workflows)} workflow(s)")
        
        # Test 4: Run workflow
        print("\n4. Running workflow...")
        run_data = {
            "workflow_id": workflow_id,
            "initial_state": {
                "count": 0,
                "quality_score": 0
            }
        }
        
        response = await client.post(f"{BASE_URL}/graph/run", json=run_data)
        assert response.status_code == 200
        run_id = response.json()["run_id"]
        print(f"   ✓ Workflow started: {run_id}")
        
        # Test 5: Poll for completion
        print("\n5. Polling for completion...")
        max_polls = 30
        poll_count = 0
        
        while poll_count < max_polls:
            await asyncio.sleep(1)
            poll_count += 1
            
            response = await client.get(f"{BASE_URL}/graph/state/{run_id}")
            assert response.status_code == 200
            
            state_data = response.json()
            status = state_data["status"]
            current_node = state_data.get("current_node")
            iteration = state_data.get("iteration_count", 0)
            
            print(f"   → Poll {poll_count}: status={status}, node={current_node}, iteration={iteration}")
            
            if status in ["completed", "failed"]:
                print(f"\n   ✓ Workflow {status}!")
                
                # Print final state
                print(f"\n6. Final State:")
                final_state = state_data["state"]
                print(f"   ✓ Count: {final_state.get('count')}")
                print(f"   ✓ Quality Score: {final_state.get('quality_score')}")
                
                # Print execution logs
                print(f"\n7. Execution Logs:")
                logs = state_data["logs"]
                print(f"   ✓ Total log entries: {len(logs)}")
                for i, log in enumerate(logs[:5], 1):  # Show first 5
                    print(f"   {i}. {log['node']}: {log['status']} (iteration: {log.get('iteration', 'N/A')})")
                
                if len(logs) > 5:
                    print(f"   ... and {len(logs) - 5} more entries")
                
                break
        
        if poll_count >= max_polls:
            print("\n   ✗ Workflow did not complete in time")
            return False
        
        # Test 6: List runs
        print("\n8. Listing workflow runs...")
        response = await client.get(f"{BASE_URL}/graph/runs?workflow_id={workflow_id}")
        assert response.status_code == 200
        runs = response.json()
        print(f"   ✓ Found {len(runs)} run(s) for this workflow")
    
    print("\n" + "=" * 60)
    print("All API integration tests passed! ✅")
    print("=" * 60)
    
    return True


async def main():
    """Run integration tests."""
    print("\n⚠️  Make sure the FastAPI server is running on http://localhost:8000")
    print("   Run: uvicorn app.main:app --reload")
    print("\n   Press Enter when ready...")
    input()
    
    try:
        success = await test_complete_workflow()
        if not success:
            print("\n❌ Tests failed")
    except Exception as e:
        print(f"\n❌ Test error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
