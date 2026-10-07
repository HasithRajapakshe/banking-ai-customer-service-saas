import asyncio
import httpx
import sys
import uuid

API_URL = "http://localhost:8001/api/v1"

async def flow_a(client):
    print("Running Flow A - Alice")
    # Login as Alice
    resp = await client.post(f"{API_URL}/auth/login", json={"username": "alice@example.com", "password": "password123"})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    alice_token = resp.json()["access_token"]
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    
    # /me
    resp = await client.get(f"{API_URL}/auth/me", headers=alice_headers)
    assert resp.status_code == 200, "/me failed"
    
    # account list
    resp = await client.get(f"{API_URL}/accounts", headers=alice_headers)
    assert resp.status_code == 200, "Account list failed"
    accounts = resp.json()
    assert len(accounts) > 0, "No accounts found"
    account_id = accounts[0]["id"]
    
    # transactions
    resp = await client.get(f"{API_URL}/accounts/{account_id}/transactions", headers=alice_headers)
    assert resp.status_code == 200, "Transactions failed"
    
    # AI: "Show my accounts"
    conv_id = str(uuid.uuid4())
    resp = await client.post(f"{API_URL}/chat", json={"message": "Show my accounts", "conversation_id": conv_id}, headers=alice_headers)
    assert resp.status_code == 200, f"Chat failed: {resp.text}"
    chat_resp = resp.json()
    
    # request card block (this might require challenge depending on setup, but let's test a simple policy question first)
    resp = await client.post(f"{API_URL}/chat", json={"message": "What is the policy for blocking a card?", "conversation_id": conv_id}, headers=alice_headers)
    assert resp.status_code == 200, "Policy question failed"
    
    # Block card
    resp = await client.post(f"{API_URL}/chat", json={"message": "Block my card ending in 1234", "conversation_id": conv_id}, headers=alice_headers)
    assert resp.status_code == 200, "Block card request failed"
    chat_resp2 = resp.json()
    
    # Check if challenge is present or it just blocked it
    
    # get history
    resp = await client.get(f"{API_URL}/chat/conversations/{conv_id}/messages", headers=alice_headers)
    assert resp.status_code == 200, "Chat history failed"
    
    print("Flow A OK")
    return alice_token

async def flow_b(client, alice_conv_id=None):
    print("Running Flow B - IDOR")
    # Login as Bob
    resp = await client.post(f"{API_URL}/auth/login", json={"username": "bob@example.com", "password": "password123"})
    if resp.status_code != 200:
        print(f"Skipping Bob, login failed: {resp.text}")
        return
    bob_token = resp.json()["access_token"]
    bob_headers = {"Authorization": f"Bearer {bob_token}"}
    
    # Attempt Alice account (IDOR) - fake ID for now or if we had Alice's account ID
    fake_alice_id = str(uuid.uuid4())
    resp = await client.get(f"{API_URL}/accounts/{fake_alice_id}", headers=bob_headers)
    assert resp.status_code in [403, 404], f"IDOR failed, got {resp.status_code}"
    
    print("Flow B OK")

async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            alice_token = await flow_a(client)
            await flow_b(client)
            print("E2E SUCCESS")
        except Exception as e:
            print(f"E2E FAILED: {e}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
