import asyncio
import httpx
import sys

API_URL = "http://localhost:8001/api/v1"

async def test_refresh_tokens():
    async with httpx.AsyncClient(timeout=30) as client:
        print("1. Login to get tokens")
        resp = await client.post(f"{API_URL}/auth/login", json={"username": "alice@example.com", "password": "password123"})
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            sys.exit(1)
        data = resp.json()
        access_token_1 = data["access_token"]
        
        print("2. Fetch /me with access_token_1")
        resp = await client.get(f"{API_URL}/auth/me", headers={"Authorization": f"Bearer {access_token_1}"})
        assert resp.status_code == 200, "/me failed"
        
        print("3. Refresh token to get access_token_2")
        print("Cookies:", client.cookies)
        resp = await client.post(f"{API_URL}/auth/refresh") # httpx client maintains the cookie
        if resp.status_code != 200:
            print(f"Refresh failed: {resp.text}")
            sys.exit(1)
        data = resp.json()
        access_token_2 = data["access_token"]
        
        print("4. Validate new access token works")
        resp = await client.get(f"{API_URL}/auth/me", headers={"Authorization": f"Bearer {access_token_2}"})
        assert resp.status_code == 200, "/me with new token failed"
        
        print("5. Logout")
        resp = await client.post(f"{API_URL}/auth/logout", headers={"Authorization": f"Bearer {access_token_2}"})
        assert resp.status_code == 200, "Logout failed"
        
        print("6. Validate refresh token is invalid after logout")
        resp = await client.post(f"{API_URL}/auth/refresh")
        assert resp.status_code in [401, 400], f"Refresh should fail, but got {resp.status_code}"
        
        print("REFRESH TOKEN TEST SUCCESS")

if __name__ == "__main__":
    asyncio.run(test_refresh_tokens())
