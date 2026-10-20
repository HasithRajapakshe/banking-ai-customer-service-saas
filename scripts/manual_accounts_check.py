import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Get token
        login_resp = await client.post("http://localhost:8001/api/v1/auth/login", json={
            "username": "alice@example.com",
            "password": "password123"
        })
        print("Login Status:", login_resp.status_code)
        token = login_resp.json().get("access_token")
        
        # Get accounts
        acc_resp = await client.get("http://localhost:8001/api/v1/accounts", headers={
            "Authorization": f"Bearer {token}"
        })
        print("Accounts Response:")
        print(acc_resp.text)

        # Get chat response
        chat_resp = await client.post("http://localhost:8001/api/v1/chat", headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }, json={
            "message": "show my balance",
            "conversation_id": "11111111-1111-1111-1111-111111111111"
        })
        print("Chat Response:")
        print(chat_resp.text)

if __name__ == "__main__":
    asyncio.run(main())
