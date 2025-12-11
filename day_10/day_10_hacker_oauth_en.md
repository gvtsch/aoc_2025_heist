Day ten. Still some missing. Information Curation.


Today is all about how the hacker agent gets exclusive bank data and shares it with the team. But he doesn’t just dump everything. He picks out what really matters and keeps the rest to himself. How do you pass on info without flooding everyone with details? That’s where information curation comes in.
The other agents have to trust the hacker, because they can’t get the bank data themselves. That’s what makes the whole thing interesting: information asymmetry and a bit of team drama, once the project is ready.

Let's get to the implementation. Some of this you already know, so I’ll just point to my repo again.

We set up the service URLs and credentials as usual:
```python
# Service URLs
OAUTH_SERVICE = "http://localhost:8001"
SIMULATION_SERVICE = "http://localhost:8003"

# Hacker's OAuth Credentials
HACKER_CLIENT_ID = "hacker-client"
HACKER_SECRET = "hacker-secret-123"
```


So, you need to start both services from day eight (OAuth Service) and day nine (Simulation Service).


I’ll skip the local LLM and token fetching part here. What’s way more interesting is the curation. After grabbing the bank data, we prep it for the LLM, like a prompt with variables for floors, vault rating, and so on. We set a word limit and could even hide, change, or highlight info at this stage. This curated string, plus a persona, goes to the LLM, and we get a compact, natural language analysis back.

Why does this matter? In real teams (and AI projects), it’s important not to just pass on raw info, but to condense, evaluate, and tailor it for your audience. That builds trust, keeps everyone from drowning in details, and helps the team actually work together.

```python
    def analyze_and_share(self) -> str:
        if not self.bank_data:
            return "No data available to analyze."

        print("\n🤖 Step 3: Analyzing Data with LLM...")

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
```

Here’s what the hacker actually gets back at first:
```bash
📂 Retrieved Bank Data:
{'data': {'name': 'First National Bank', 'address': '123 Main Street', 'floors': 3, 'vault_rating': 'TL-30', 'security_systems': ['CCTV', 'Motion Sensors', 'Alarm'], 'guard_count': 4}, 'access_granted_to': 'hacker-client', 'scope': 'simulation:read'}
```

After curation, we get a compact, readable response in plain English:
```bash
📊 Security Analysis:
------------------------------------------------------------
## First National Bank Security Analysis:

**Strengths:** Robust physical security with TL-30 vault, layered defenses (CCTV, motion, alarms), and dedicated guards.

**Challenges:**  Limited information on guard training/response protocols & system redundancy. Potential vulnerabilities exist in human element (guard reliability) and reliance on standard systems.  Insider threat assessment is missing. Further risk assessment needed for comprehensive security posture.
```


And that’s pretty much it for today’s door.

## Summary




Oh, and by the way: this whole setup also opens up some interesting options for the mole. If someone on the inside wants to twist, hide, or leak information, information asymmetry and curation make it possible. Trust is good, but sometimes, a little paranoia is part of the game.

So, what sticks today? The hacker gets the bank data, but he decides what the team really gets to know. Not everything gets thrown out there, just what’s curated, condensed, and packaged up. The others have to trust him, and that’s what makes things interesting: Who shares what, how much, and how honest is it, really? Information curation isn’t just some buzzword, it’s the secret sauce for good teamwork, whether you’re building AI or just working with people. Sometimes, less is more. That’s it for today’s door!
