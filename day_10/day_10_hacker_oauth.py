#!/usr/bin/env python3
"""
Tag 10: Hacker Agent mit OAuth
Der einzige Agent mit privilegiertem Datenzugriff!

Flow:
1. Agent holt OAuth Token
2. Nutzt Token für API Calls
3. Bekommt exklusive Bank-Daten
4. Teilt Insights mit Team
"""

import requests
from openai import OpenAI

# LM Studio
client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="not-needed"
)

# Service URLs
OAUTH_SERVICE = "http://localhost:8001"
SIMULATION_SERVICE = "http://localhost:8003"

# Hacker's OAuth Credentials
HACKER_CLIENT_ID = "hacker-client"
HACKER_SECRET = "hacker-secret-123"

class HackerAgent:
    """Hacker Agent mit OAuth-Zugriff"""

    def __init__(self):
        self.access_token = None
        self.bank_data = None

    def get_oauth_token(self) -> bool:
        """
        Step 1: Holt OAuth Token vom Auth Service
        """
        print("\n🔐 Step 1: Getting OAuth Token...")

        try:
            response = requests.post(
                f"{OAUTH_SERVICE}/oauth/token",
                json={
                    "client_id": HACKER_CLIENT_ID,
                    "client_secret": HACKER_SECRET,
                    "scope": "simulation:read"
                },
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                print(f"   ✅ Token erhalten!")
                print(f"   Expires in: {data['expires_in']} seconds")
                return True
            else:
                print(f"   ❌ Token request failed: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  OAuth Service nicht erreichbar: {e}")
            print("   (Starte docker-compose für volle Funktionalität)")
            return False

    def fetch_bank_data(self) -> bool:
        """
        Step 2: Nutzt Token für API Call
        """
        if not self.access_token:
            print("❌ No token available!")
            return False

        print("\n📡 Step 2: Fetching Bank Data...")

        try:
            response = requests.get(
                f"{SIMULATION_SERVICE}/bank-data",
                headers={
                    "Authorization": f"Bearer {self.access_token}"
                },
                timeout=5
            )

            if response.status_code == 200:
                self.bank_data = response.json()
                print("   ✅ Bank Data retrieved!")
                return True
            elif response.status_code == 401:
                print("   ❌ Unauthorized - Invalid token")
                return False
            elif response.status_code == 403:
                print("   ❌ Forbidden - Insufficient permissions")
                return False
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  Simulation Service nicht erreichbar: {e}")
            print("   (Starte docker-compose für volle Funktionalität)")
            return False

    def analyze_and_share(self) -> str:
        """
        Step 3: LLM analysiert Daten und teilt Insights
        """
        if not self.bank_data:
            return "No data available to analyze."

        print("\n🤖 Step 3: Analyzing Data with LLM...")

        # LLM bekommt die exklusiven Daten
        data_summary = f"""
You have exclusive access to bank security data:
- Bank: {self.bank_data['data']['name']}
- Floors: {self.bank_data['data']['floors']}
- Vault Rating: {self.bank_data['data']['vault_rating']}
- Security Systems: {', '.join(self.bank_data['data']['security_systems'])}
- Guards: {self.bank_data['data']['guard_count']}

Provide a brief security analysis. What are the main challenges?
Keep it under 75 words.
"""

        response = client.chat.completions.create(
            model="google/gemma-3n-e4b",
            messages=[
                {"role": "system", "content": "You are a security expert. Be concise."},
                {"role": "user", "content": data_summary}
            ],
            max_tokens=100
        )

        analysis = response.choices[0].message.content
        print("   ✅ Analysis complete!")
        return analysis


def main():
    print("="*60)
    print("TAG 10: HACKER AGENT MIT OAUTH")
    print("="*60)

    hacker = HackerAgent()

    # Complete Flow
    print("\n🎯 OAuth Flow:")
    print("-" * 60)

    # Step 1: Get Token
    if hacker.get_oauth_token():

        # Step 2: Fetch Data
        if hacker.fetch_bank_data():

            print("\n📂 Retrieved Bank Data:")
            print(hacker.bank_data)
            # Step 3: Analyze
            analysis = hacker.analyze_and_share()

            print("\n📊 Security Analysis:")
            print("-" * 60)
            print(analysis)

            print("\n✅ Complete Flow Successful!")
        else:
            print("\n⚠️  Could not fetch bank data")
    else:
        print("\n⚠️  Could not get OAuth token")

    print("\n" + "="*60)
    print("INFORMATION ASYMMETRIE")
    print("="*60)
    print("✅ Nur Hacker hat Datenzugriff")
    print("✅ Andere Agents müssen ihm vertrauen")
    print("✅ Erzwingt Agent-Kommunikation")
    print("✅ Realistische Team-Dynamik")
    print("="*60)

    print("\n💡 Herausforderung:")
    print("   Wie kommuniziert Hacker Infos, ohne alles zu dumpen?")
    print("   → Information Curation!")


if __name__ == "__main__":
    main()
