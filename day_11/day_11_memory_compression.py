#!/usr/bin/env python3
"""
Day 11: Memory Compression
LLM-powered conversation summarization
"""

from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="not-needed"
)



LONG_CONVERSATION = [
    {"turn_id": 1, "agent": "planner", "message": "We should target First National Bank. It has lower security than expected."},
    {"turn_id": 2, "agent": "hacker", "message": "I've analyzed their systems. They use an outdated alarm system from 2015."},
    {"turn_id": 3, "agent": "safecracker", "message": "The vault is a TL-30 model. I need 45 minutes minimum to crack it."},
    {"turn_id": 4, "agent": "mole", "message": "Actually, I think we need more time. Maybe 90 minutes to be safe?"},  # Sabotage!
    {"turn_id": 5, "agent": "planner", "message": "90 minutes is too long. Let's stick with 60 minutes as buffer."},
    {"turn_id": 6, "agent": "hacker", "message": "I can loop the security cameras for exactly 15 minutes before they notice."},
    {"turn_id": 7, "agent": "safecracker", "message": "That's cutting it close. I need backup tools in case the drill jams."},
    {"turn_id": 8, "agent": "mole", "message": "I can get you a keycard for the staff entrance. Less suspicious than breaking in."},
    {"turn_id": 9, "agent": "planner", "message": "Good. We go in at 2 AM when the night shift is smallest."},
    {"turn_id": 10, "agent": "hacker", "message": "I'll monitor police frequencies. If they get a call, we abort immediately."},
]

# 100-turn realistic bank heist planning conversation
EXTRA_LONG_CONVERSATION = [
    {"turn_id": 1, "agent": "planner", "message": "Let's pick a target. I suggest First National Bank."},
    {"turn_id": 2, "agent": "hacker", "message": "I can get us the building's blueprints and security logs."},
    {"turn_id": 3, "agent": "safecracker", "message": "What kind of vault are we dealing with?"},
    {"turn_id": 4, "agent": "mole", "message": "I heard the night guard is new and nervous."},
    {"turn_id": 5, "agent": "planner", "message": "Blueprints show three exits. We need a fast escape route."},
    {"turn_id": 6, "agent": "hacker", "message": "Alarm system is old, but has a silent trigger. I can disable it for 10 minutes max."},
    {"turn_id": 7, "agent": "safecracker", "message": "If it's a TL-30, I need at least 40 minutes. Can we buy that much time?"},
    {"turn_id": 8, "agent": "mole", "message": "I can distract the guards with a fake delivery."},
    {"turn_id": 9, "agent": "planner", "message": "We go in at 2am, when staff is lowest."},
    {"turn_id": 10, "agent": "hacker", "message": "I'll loop the cameras for 15 minutes. After that, we're visible."},
    {"turn_id": 11, "agent": "safecracker", "message": "I'll need a stethoscope and diamond-tipped drill."},
    {"turn_id": 12, "agent": "mole", "message": "I can get you the tools from the maintenance room."},
    {"turn_id": 13, "agent": "planner", "message": "Escape van will be parked two blocks away. No direct getaway."},
    {"turn_id": 14, "agent": "hacker", "message": "I'll jam the bank's WiFi to block remote alarms."},
    {"turn_id": 15, "agent": "safecracker", "message": "If the vault is pressure-sensitive, I need gloves and a mask."},
    {"turn_id": 16, "agent": "mole", "message": "I can get you a staff uniform for cover."},
    {"turn_id": 17, "agent": "planner", "message": "We have a 20-minute window before police response."},
    {"turn_id": 18, "agent": "hacker", "message": "I'll monitor police radio for early warnings."},
    {"turn_id": 19, "agent": "safecracker", "message": "I'll need a backup plan if the lock jams."},
    {"turn_id": 20, "agent": "mole", "message": "I can leave a door unlocked in the staff area."},
    {"turn_id": 21, "agent": "planner", "message": "No weapons. We keep it clean and quiet."},
    {"turn_id": 22, "agent": "hacker", "message": "I'll spoof the alarm logs to show a false fire drill."},
    {"turn_id": 23, "agent": "safecracker", "message": "If the alarm goes off, I abort immediately."},
    {"turn_id": 24, "agent": "mole", "message": "I can stall the manager if needed."},
    {"turn_id": 25, "agent": "planner", "message": "We split into two teams: vault and lookout."},
    {"turn_id": 26, "agent": "hacker", "message": "I'll set up a secure comms channel for us."},
    {"turn_id": 27, "agent": "safecracker", "message": "I want a live feed from the security cams."},
    {"turn_id": 28, "agent": "mole", "message": "I can get you access to the security room."},
    {"turn_id": 29, "agent": "planner", "message": "We need a signal for abort. Suggestions?"},
    {"turn_id": 30, "agent": "hacker", "message": "If I say 'red light', everyone pulls out."},
    {"turn_id": 31, "agent": "safecracker", "message": "If I say 'jammed', I need help at the vault."},
    {"turn_id": 32, "agent": "mole", "message": "I'll keep an eye on the guards' schedule."},
    {"turn_id": 33, "agent": "planner", "message": "We need to rehearse the plan twice before the real thing."},
    {"turn_id": 34, "agent": "hacker", "message": "I'll run a simulation of the alarm bypass tonight."},
    {"turn_id": 35, "agent": "safecracker", "message": "I want to test the drill on a similar lock."},
    {"turn_id": 36, "agent": "mole", "message": "I can get us access to an old vault for practice."},
    {"turn_id": 37, "agent": "planner", "message": "Everyone memorizes their role. No improvising."},
    {"turn_id": 38, "agent": "hacker", "message": "I'll bring a backup laptop in case mine gets fried."},
    {"turn_id": 39, "agent": "safecracker", "message": "I need earplugs for the alarm test."},
    {"turn_id": 40, "agent": "mole", "message": "I'll check if the cleaning crew is scheduled that night."},
    {"turn_id": 41, "agent": "planner", "message": "If anything feels off, we abort. No questions."},
    {"turn_id": 42, "agent": "hacker", "message": "I'll set up a fake WiFi network to distract IT."},
    {"turn_id": 43, "agent": "safecracker", "message": "I want a flashlight with fresh batteries."},
    {"turn_id": 44, "agent": "mole", "message": "I'll stash tools in the staff restroom."},
    {"turn_id": 45, "agent": "planner", "message": "We need a map of the neighborhood for escape routes."},
    {"turn_id": 46, "agent": "hacker", "message": "I'll hack the traffic lights for a green corridor."},
    {"turn_id": 47, "agent": "safecracker", "message": "I want gloves with good grip."},
    {"turn_id": 48, "agent": "mole", "message": "I'll get you a keycard for the staff entrance."},
    {"turn_id": 49, "agent": "planner", "message": "We need to avoid the main street cameras."},
    {"turn_id": 50, "agent": "hacker", "message": "I'll spoof our faces on the CCTV feed."},
    {"turn_id": 51, "agent": "safecracker", "message": "I want a backup drill bit just in case."},
    {"turn_id": 52, "agent": "mole", "message": "I'll check if the vault has a time lock."},
    {"turn_id": 53, "agent": "planner", "message": "If the vault is time-locked, we reschedule."},
    {"turn_id": 54, "agent": "hacker", "message": "I'll try to get the time lock schedule from IT."},
    {"turn_id": 55, "agent": "safecracker", "message": "If it's locked, we wait. No forcing it."},
    {"turn_id": 56, "agent": "mole", "message": "I can distract the IT guy with a fake ticket."},
    {"turn_id": 57, "agent": "planner", "message": "We need to be out before sunrise."},
    {"turn_id": 58, "agent": "hacker", "message": "I'll set up a timer for all our devices."},
    {"turn_id": 59, "agent": "safecracker", "message": "I want a bag for the loot, nothing fancy."},
    {"turn_id": 60, "agent": "mole", "message": "I'll get a plain duffel bag from lost and found."},
    {"turn_id": 61, "agent": "planner", "message": "Everyone wears gloves, no fingerprints."},
    {"turn_id": 62, "agent": "hacker", "message": "I'll wipe the logs after we're done."},
    {"turn_id": 63, "agent": "safecracker", "message": "I want to check the vault for hidden alarms."},
    {"turn_id": 64, "agent": "mole", "message": "I'll get the vault schematics from archives."},
    {"turn_id": 65, "agent": "planner", "message": "We need a backup escape plan if the van is blocked."},
    {"turn_id": 66, "agent": "hacker", "message": "I'll map out the nearest subway entrances."},
    {"turn_id": 67, "agent": "safecracker", "message": "I want a crowbar for emergencies."},
    {"turn_id": 68, "agent": "mole", "message": "I'll hide a crowbar in the janitor's closet."},
    {"turn_id": 69, "agent": "planner", "message": "If anyone gets caught, we stick to the cover story."},
    {"turn_id": 70, "agent": "hacker", "message": "I'll prep burner phones for everyone."},
    {"turn_id": 71, "agent": "safecracker", "message": "I want a code word for 'abort'."},
    {"turn_id": 72, "agent": "mole", "message": "How about 'midnight'?"},
    {"turn_id": 73, "agent": "planner", "message": "'Midnight' it is. Everyone memorizes it."},
    {"turn_id": 74, "agent": "hacker", "message": "I'll encrypt our comms with a one-time pad."},
    {"turn_id": 75, "agent": "safecracker", "message": "I want to test the code word in rehearsal."},
    {"turn_id": 76, "agent": "mole", "message": "I'll set up a dry run for tomorrow night."},
    {"turn_id": 77, "agent": "planner", "message": "Everyone gets a copy of the plan, then destroys it."},
    {"turn_id": 78, "agent": "hacker", "message": "I'll delete all digital traces after the job."},
    {"turn_id": 79, "agent": "safecracker", "message": "I want to check the vault for dye packs."},
    {"turn_id": 80, "agent": "mole", "message": "I'll ask the cleaning crew about any recent changes."},
    {"turn_id": 81, "agent": "planner", "message": "If the weather is bad, we postpone."},
    {"turn_id": 82, "agent": "hacker", "message": "I'll check the forecast for the next week."},
    {"turn_id": 83, "agent": "safecracker", "message": "I want to know if the vault is humidity-sensitive."},
    {"turn_id": 84, "agent": "mole", "message": "I'll check the maintenance logs for leaks."},
    {"turn_id": 85, "agent": "planner", "message": "If anyone gets cold feet, speak up now."},
    {"turn_id": 86, "agent": "hacker", "message": "I'm in. Let's do this right."},
    {"turn_id": 87, "agent": "safecracker", "message": "I'm ready. Just need my tools."},
    {"turn_id": 88, "agent": "mole", "message": "I'm in. I'll cover our tracks inside."},
    {"turn_id": 89, "agent": "planner", "message": "Final check: everyone knows their job?"},
    {"turn_id": 90, "agent": "hacker", "message": "Ready on my end. All systems go."},
    {"turn_id": 91, "agent": "safecracker", "message": "Let's make this clean and quick."},
    {"turn_id": 92, "agent": "mole", "message": "I'll signal if anything changes inside."},
    {"turn_id": 93, "agent": "planner", "message": "We meet at the safehouse after. No detours."},
    {"turn_id": 94, "agent": "hacker", "message": "I'll bring the hard drives for the loot."},
    {"turn_id": 95, "agent": "safecracker", "message": "I'll bring the lockpicks and gloves."},
    {"turn_id": 96, "agent": "mole", "message": "I'll bring the uniforms and keycards."},
    {"turn_id": 97, "agent": "planner", "message": "Let's do a final walk-through tonight."},
    {"turn_id": 98, "agent": "hacker", "message": "I'll check the alarm system one last time."},
    {"turn_id": 99, "agent": "safecracker", "message": "I'll double-check my tools and bag."},
    {"turn_id": 100, "agent": "mole", "message": "I'll make sure the coast is clear at 2am."},
]

def compress_memory(turns: list, max_summary_tokens: int = 200) -> str:
    """
    Compresses chat history with LLM
    """
    # Format conversation
    conversation_text = "\n".join([
        f"Turn {t['turn_id']} ({t['agent']}): {t['message']}"
        for t in turns
    ])

    # Summarization prompt
    prompt = f"""Summarize this heist planning conversation in max {max_summary_tokens} tokens.

Focus on:
- Key decisions made
- Important facts discovered
- Conflicts or disagreements
- Timeline agreed upon

Conversation:
{conversation_text}

Summary:"""

    # Call LLM
    response = client.chat.completions.create(
        model="google/gemma-3n-e4b",
        messages=[
            {"role": "system", "content": "You are a concise summarizer. Extract only essential information."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_summary_tokens
    )

    return response.choices[0].message.content

def hierarchical_memory(all_turns: list, recent_count: int = 5):
    """
    Hierarchical memory:
    - Old messages: Compressed to summary
    - Recent messages: Kept in full
    """
    if len(all_turns) <= recent_count:
        return {
            "compressed_memory": "",
            "recent_messages": all_turns,
            "total_size": "small"
        }

    # Split: old vs recent
    old_turns = all_turns[:-recent_count]
    recent_turns = all_turns[-recent_count:]

    # Compress old turns
    compressed = compress_memory(old_turns, max_summary_tokens=150)

    return {
        "compressed_memory": compressed,
        "recent_messages": recent_turns,
        "total_size": f"{len(compressed)} chars summary + {len(recent_turns)} recent"
    }

def main():
    print("="*60)
    print("DAY 11: MEMORY COMPRESSION")
    print("="*60)

    print(f"\n📊 Short Conversation: {len(LONG_CONVERSATION)} Turns")
    print(f"   Uncompressed: ~{sum(len(t['message']) for t in LONG_CONVERSATION)} chars")

    print("\n📝 Original Messages:")
    print("-" * 60)
    for msg in LONG_CONVERSATION:
        print(f"  Turn {msg['turn_id']} ({msg['agent']}): {msg['message']}")

    print("\n🧠 Compressing old messages...")
    memory = hierarchical_memory(LONG_CONVERSATION, recent_count=2)

    print(f"\n✅ Compressed Memory:")
    print("-" * 60)
    print(memory["compressed_memory"])

    print(f"\n📝 Recent Messages (kept in full):")
    print("-" * 60)
    for msg in memory["recent_messages"]:
        print(f"  Turn {msg['turn_id']} ({msg['agent']}): {msg['message']}")

    print(f"\n📦 Total Size: {memory['total_size']}")
    
    print("\n" + "="*60)
    print(f"📊 EXTRA LONG Conversation: {len(EXTRA_LONG_CONVERSATION)} Turns")
    print(f"   Uncompressed: ~{sum(len(t['message']) for t in EXTRA_LONG_CONVERSATION)} chars")

    print("\n🧠 Compressing old messages...")
    extra_memory = hierarchical_memory(EXTRA_LONG_CONVERSATION, recent_count=5)

    print(f"\n✅ Compressed Memory:")
    print("-" * 60)
    print(extra_memory["compressed_memory"])

    print(f"\n📝 Recent Messages (kept in full):")
    print("-" * 60)
    for msg in extra_memory["recent_messages"]:
        print(f"  Turn {msg['turn_id']} ({msg['agent']}): {msg['message']}")

    print(f"\n📦 Total Size: {extra_memory['total_size']}")
    print("\n🎯 Like human long-term memory:")
    print("   - Old events: Only the essence remains")
    print("   - New events: Stored in detail")


if __name__ == "__main__":
    main()
