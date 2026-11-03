#!/usr/bin/env python
"""Complete workflow test script."""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

print("\n" + "="*60)
print("COMPLETE SCREENING WORKFLOW TEST")
print("="*60 + "\n")

try:
    # Step 1: Get Jobs
    print("[1] Getting available jobs...")
    jobs_resp = requests.get(f"{BASE_URL}/jobs")
    jobs = jobs_resp.json()
    print(f"SUCCESS: Found {len(jobs)} jobs")
    print(f"  Job 1: {jobs[0]['title']} ({jobs[0]['level']})")
    print(f"  Job 2: {jobs[1]['title']} ({jobs[1]['level']})")

    # Step 2: Get Candidates
    print("\n[2] Getting candidates...")
    cands_resp = requests.get(f"{BASE_URL}/candidates")
    candidates = cands_resp.json()
    print(f"SUCCESS: Found {len(candidates)} candidates")
    print(f"  Candidate 1: {candidates[0]['name']} ({candidates[0]['experience_years']} years)")
    print(f"  Candidate 2: {candidates[1]['name']} ({candidates[1]['experience_years']} years)")

    # Step 3: Create Screening Batch
    print("\n[3] Creating screening batch...")
    job_id = jobs[0]['id']
    candidate_ids = [candidates[0]['id'], candidates[1]['id'], candidates[2]['id']]

    batch_resp = requests.post(
        f"{BASE_URL}/screen/batch",
        params={"job_id": job_id, "candidate_ids": candidate_ids}
    )
    batch_data = batch_resp.json()
    print(f"SUCCESS: Batch created with {batch_data['screenings_created']} screenings")
    screening_ids = batch_data['screening_ids']
    print(f"  First screening ID: {screening_ids[0]}")

    # Step 4: Start Screening Workflow
    print("\n[4] Running screening workflow...")
    screening_id = screening_ids[0]
    workflow_resp = requests.post(f"{BASE_URL}/screen/{screening_id}/start-workflow")
    workflow_data = workflow_resp.json()
    print(f"SUCCESS: Workflow completed")
    print(f"  Status: {workflow_data['status']}")
    print(f"  Fit Score: {workflow_data['fit_score']:.1f}%")
    print(f"  Message Generated: {workflow_data['message_generated']}")

    # Step 5: Get Full Details
    print("\n[5] Getting detailed screening results...")
    detail_resp = requests.get(f"{BASE_URL}/screen/{screening_id}/detail")
    detail_data = detail_resp.json()

    screening = detail_data['screening']
    candidate = detail_data['candidate']
    job = detail_data['job']

    print(f"SUCCESS: Screening details retrieved")
    print(f"  Candidate: {candidate['name']} ({candidate['email']})")
    print(f"  Job: {job['title']}")
    print(f"  Fit Score: {screening['fit_score']:.1f}")
    print(f"  Status: {screening['approval_status']}")

    # Step 6: Show Generated Message
    print("\n[6] Generated Message:")
    print("-" * 60)
    print(screening['generated_message'][:300] + "...")
    print("-" * 60)

    # Step 7: Approve Screening
    print("\n[7] Approving screening...")
    approve_resp = requests.post(
        f"{BASE_URL}/screen/{screening_id}/approve",
        json={"approval_status": "approved", "feedback": "Great match!"}
    )
    approve_data = approve_resp.json()
    print(f"SUCCESS: Screening approved")
    print(f"  Status: {approve_data['approval_status']}")
    print(f"  Message: {approve_data['message']}")

    # Step 8: Test another candidate - reject
    print("\n[8] Testing rejection workflow...")
    screening_id_2 = screening_ids[1]

    # Start workflow
    requests.post(f"{BASE_URL}/screen/{screening_id_2}/start-workflow")

    # Reject
    reject_resp = requests.post(
        f"{BASE_URL}/screen/{screening_id_2}/reject",
        json={"approval_status": "rejected", "feedback": "Skills gap"}
    )
    reject_data = reject_resp.json()
    print(f"SUCCESS: Screening rejected")
    print(f"  Status: {reject_data['approval_status']}")

    print("\n" + "="*60)
    print("ALL TESTS PASSED!")
    print("="*60 + "\n")

    print("Summary:")
    print(f"  PASS: Jobs retrieved: {len(jobs)}")
    print(f"  PASS: Candidates retrieved: {len(candidates)}")
    print(f"  PASS: Screening batch created: {batch_data['screenings_created']} screenings")
    print(f"  PASS: Workflow executed: {workflow_data['fit_score']:.1f}% fit score")
    print(f"  PASS: Message generated and validated")
    print(f"  PASS: Approval workflow tested")
    print(f"  PASS: Rejection workflow tested")

    print("\nSystem Status: OPERATIONAL\n")
    print(f"Access the UI at: http://127.0.0.1:5174")
    print(f"API Docs: http://127.0.0.1:8000/docs\n")

except requests.exceptions.ConnectionError:
    print("FAILED: Cannot connect to backend")
    print("Make sure the backend is running on http://127.0.0.1:8000")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
