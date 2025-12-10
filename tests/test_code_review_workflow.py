"""
End-to-end test for Code Review Workflow.
"""

import asyncio
import httpx
from app.workflows.code_review_workflow import (
    get_code_review_workflow,
    SAMPLE_CODE_GOOD,
    SAMPLE_CODE_BAD
)


BASE_URL = "http://localhost:8000/api/v1"


async def test_code_review_workflow(code: str, test_name: str):
    """Test code review workflow with given code."""
    
    print("\n" + "=" * 70)
    print(f"Testing: {test_name}")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # Step 1: Create workflow
        print("\n1. Creating code review workflow...")
        workflow_data = get_code_review_workflow()
        
        response = await client.post(f"{BASE_URL}/graph/create", json=workflow_data)
        if response.status_code != 200:
            print(f"   ✗ Failed to create workflow: {response.text}")
            return False
        
        workflow_id = response.json()["workflow_id"]
        print(f"   ✓ Workflow created: {workflow_id}")
        
        # Step 2: Run workflow
        print("\n2. Running code review...")
        print(f"   Code length: {len(code)} characters")
        print(f"   Code preview: {code[:100]}...")
        
        run_data = {
            "workflow_id": workflow_id,
            "initial_state": {
                "code": code,
                "functions": [],
                "complexity_scores": {},
                "issues": [],
                "quality_score": 0,
                "suggestions": [],
                "improvements_applied": 0
            }
        }
        
        response = await client.post(f"{BASE_URL}/graph/run", json=run_data)
        if response.status_code != 200:
            print(f"   ✗ Failed to start workflow: {response.text}")
            return False
        
        run_id = response.json()["run_id"]
        print(f"   ✓ Workflow started: {run_id}")
        
        # Step 3: Poll for completion
        print("\n3. Monitoring execution...")
        max_polls = 60
        poll_count = 0
        
        while poll_count < max_polls:
            await asyncio.sleep(1)
            poll_count += 1
            
            response = await client.get(f"{BASE_URL}/graph/state/{run_id}")
            if response.status_code != 200:
                print(f"   ✗ Failed to get state: {response.text}")
                return False
            
            state_data = response.json()
            status = state_data["status"]
            current_node = state_data.get("current_node", "unknown")
            iteration = state_data.get("iteration_count", 0)
            
            print(f"   → Poll {poll_count}: status={status}, node={current_node}, iteration={iteration}")
            
            if status in ["completed", "failed"]:
                print(f"\n   ✓ Workflow {status}!")
                
                # Step 4: Analyze results
                print("\n4. Results:")
                final_state = state_data["state"]
                
                functions = final_state.get('functions', [])
                issues = final_state.get('issues', [])
                quality_score = final_state.get('quality_score', 0)
                improvements = final_state.get('improvements_applied', 0)
                
                print(f"\n   Functions Found: {len(functions)}")
                for func in functions:
                    print(f"      - {func['name']}: {func['code_line_count']} lines, "
                          f"complexity {final_state.get('complexity_scores', {}).get(func['name'], 'N/A')}")
                
                print(f"\n   Issues Detected: {len(issues)}")
                issue_counts = {}
                for issue in issues:
                    issue_type = issue['type']
                    issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
                
                for issue_type, count in issue_counts.items():
                    print(f"      - {issue_type}: {count}")
                
                print(f"\n   Quality Score: {quality_score}/10")
                print(f"   Improvements Applied: {improvements}")
                print(f"   Total Iterations: {iteration}")
                
                # Step 5: Show execution timeline
                print("\n5. Execution Timeline:")
                logs = state_data["logs"]
                print(f"   Total log entries: {len(logs)}")
                
                for i, log in enumerate(logs[:10], 1):
                    iter_info = f" (iter {log['iteration']})" if log.get('iteration') else ""
                    duration = f" [{log['duration_ms']}ms]" if log.get('duration_ms') else ""
                    print(f"   {i}. {log['node']}: {log['status']}{iter_info}{duration}")
                
                if len(logs) > 10:
                    print(f"   ... and {len(logs) - 10} more entries")
                
                # Show error if failed
                if status == "failed":
                    error = state_data.get('error_message', 'Unknown error')
                    print(f"\n   ✗ Error: {error}")
                
                return status == "completed"
        
        print("\n   ✗ Workflow did not complete in time")
        return False


async def main():
    """Run all tests."""
    
    print("\n" + "=" * 70)
    print("CODE REVIEW WORKFLOW - END-TO-END TEST")
    print("=" * 70)
    
    print("\n⚠️  Make sure the FastAPI server is running on http://localhost:8000")
    print("   Run: uvicorn app.main:app --reload")
    print("\n   Press Enter when ready...")
    input()
    
    try:
        # Test 1: Good code (should pass quickly)
        print("\n" + "=" * 70)
        print("TEST 1: GOOD CODE (Expected: High quality score)")
        print("=" * 70)
        success1 = await test_code_review_workflow(SAMPLE_CODE_GOOD, "Good Code Test")
        
        # Test 2: Bad code (should iterate multiple times)
        print("\n" + "=" * 70)
        print("TEST 2: BAD CODE (Expected: Multiple iterations)")
        print("=" * 70)
        success2 = await test_code_review_workflow(SAMPLE_CODE_BAD, "Bad Code Test")
        
        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"   Test 1 (Good Code): {'✅ PASSED' if success1 else '❌ FAILED'}")
        print(f"   Test 2 (Bad Code): {'✅ PASSED' if success2 else '❌ FAILED'}")
        
        if success1 and success2:
            print("\n🎉 All tests passed!")
        else:
            print("\n❌ Some tests failed")
        
    except Exception as e:
        print(f"\n❌ Test error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
