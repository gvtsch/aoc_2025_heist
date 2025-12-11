Day eleven brings something to the table that's especially important for locally hosted LLMs. How do I get my entire conversation into the context window? This might not be a big problem in our current project, but in professional environments, context grows rapidly and you have to compress it in some sensible and reliable way. That's a discipline made for LLMs ;)

A quick breakdown: Our hardware and the models we use only allow a certain context size, measured in tokens. Since the model often already takes up a considerable part of GPU memory (or unified RAM on Apple Silicon), we can pass at most as many tokens as still fit into memory. Or as many as the LLM allows, because they also have limits on the number of tokens they can process.

Today's goal is therefore to reduce the number of tokens. You could simply discard old messages (token windowing) or work with a sliding window (keeping the last X messages). Both variants cause data to be lost though. That's why we're trying it hierarchically: Old messages are summarized, new ones remain complete.

Let's get to the implementation!
I had two conversations generated. What the agents discuss wasn't formulated by me, but by an LLM. A short conversation that we can also follow the content of, and a longer one that's ultimately just about statistics. The shorter conversation consists of ten sentences stored in a dict:

```python
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
````

You can also torture yourself with the longer conversation of 100 sentences, I'll pass 😉 You'll find the conversation in the repo.

Two functions follow now. First, the one for compressing the data.

```python
def compress_memory(turns: list, max_summary_tokens: int = 200) -> str:

    conversation_text = "\n".join([
        f"Turn {t['turn_id']} ({t['agent']}): {t['message']}"
        for t in turns
    ])

    prompt = f"""Summarize this heist planning conversation in max {max_summary_tokens} tokens.

Focus on:
- Key decisions made
- Important facts discovered
- Conflicts or disagreements
- Timeline agreed upon

Conversation:
{conversation_text}

Summary:"""

    response = client.chat.completions.create(
        model="google/gemma-3n-e4b",
        messages=[
            {"role": "system", "content": "You are a concise summarizer. Extract only essential information."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_summary_tokens
    )

    return response.choices[0].message.content
```

We know this game by now. We define a prompt, enrich it with content and pass it along with the system message to the locally hosted LLM. In this case, we also pass the maximum number of tokens for the response/summary as a variable in the prompt and of course the conversation we composed earlier.

This function is called by the following function for hierarchical memory. It's basically modeled after humans. We remember the core themes and decisions from the last meeting, but not every sentence said.

And we can use this in many ways. Whenever conversations get longer. A downside is of course that it requires an explicit LLM call. And sometimes important information still gets lost. Incidentally, coding assistants also frequently support such memory compression techniques.

```python
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
```

Now let's look at the results. For the shorter conversation, we get the following output:

```bash
============================================================
DAY 11: MEMORY COMPRESSION
============================================================

📊 Short Conversation: 10 Turns
   Uncompressed: ~693 chars

📝 Original Messages:
------------------------------------------------------------
  Turn 1 (planner): We should target First National Bank. It has lower security than expected.
  Turn 2 (hacker): I've analyzed their systems. They use an outdated alarm system from 2015.
  Turn 3 (safecracker): The vault is a TL-30 model. I need 45 minutes minimum to crack it.
  Turn 4 (mole): Actually, I think we need more time. Maybe 90 minutes to be safe?
  Turn 5 (planner): 90 minutes is too long. Let's stick with 60 minutes as buffer.
  Turn 6 (hacker): I can loop the security cameras for exactly 15 minutes before they notice.
  Turn 7 (safecracker): That's cutting it close. I need backup tools in case the drill jams.
  Turn 8 (mole): I can get you a keycard for the staff entrance. Less suspicious than breaking in.
  Turn 9 (planner): Good. We go in at 2 AM when the night shift is smallest.
  Turn 10 (hacker): I'll monitor police frequencies. If they get a call, we abort immediately.

🧠 Compressing old messages...

✅ Compressed Memory:
------------------------------------------------------------
Heist target: First National Bank (low security). Vault: TL-30 (45 min crack). Timeline: 60 min (buffer, compromise). Hacker can loop cameras (15 min). Mole offers staff keycard for less suspicious entry. Safecracker needs backup tools. Disagreement on time: 45 min (safecracker) vs. 90 min (mole), settled on 60 min.


📝 Recent Messages (kept in full):
------------------------------------------------------------
  Turn 9 (planner): Good. We go in at 2 AM when the night shift is smallest.
  Turn 10 (hacker): I'll monitor police frequencies. If they get a call, we abort immediately.

📦 Total Size: 318 chars summary + 2 recent
```

From about 700 characters we got slim 318 words plus the last two sentences. If you add it all up, you haven't gained much yet, but for demonstrating how it works it should fit and is still comprehensible. But to show that this approach works well, especially with larger context, we have the even longer conversation. And that comes out to:

```bash
============================================================
📊 EXTRA LONG Conversation: 100 Turns
   Uncompressed: ~4359 chars

🧠 Compressing old messages...

✅ Compressed Memory:
------------------------------------------------------------
A team plans a bank heist at First National Bank, targeting a vault with a potentially time-sensitive lock. The plan involves the hacker disabling alarms (10 min), the safecracker opening the vault (40+ min), and the mole providing inside access & distraction.  The team aims for a 2 AM entry, with a 20-minute window before police response.  They have backup plans for various contingencies, including abort signals ("midnight"), and a 2-day rehearsal schedule.  Escape involves a van two blocks away, with the hacker preparing for traffic manipulation and digital cleanup.


📝 Recent Messages (kept in full):
------------------------------------------------------------
  Turn 96 (mole): I'll bring the uniforms and keycards.
  Turn 97 (planner): Let's do a final walk-through tonight.
  Turn 98 (hacker): I'll check the alarm system one last time.
  Turn 99 (safecracker): I'll double-check my tools and bag.
  Turn 100 (mole): I'll make sure the coast is clear at 2am.

📦 Total Size: 575 chars summary + 5 recent
```

In this case, over 4000 characters became just under 600 plus the 5 sentences. So it's significantly less context that I have to drag around in the future. Especially important for local LLMs. And ultimately it also resembles human behavior somehow.

## Summary

We've programmed a kind of hierarchical memory for information compression. This memory resembles our human brain in some way. Old things become blurry or are completely forgotten, while the important and most recent things continue to persist in memory. For long conversations with LLMs, this is really worth its weight in gold. You save tokens, time and money in the long run without losing the thread.

On the other hand, each compression initially costs one LLM call of course. In the long term it becomes more efficient. And for local LLMs with little memory, this is often the only way to process longer contexts.

Concretely, this means our agents could plan for hours without the LLM being overwhelmed or forgetting important decisions.

## Outlook: Where's the journey heading?

What we built today is just the beginning. Memory compression is a powerful tool, but there's more to come:

**Persistent memories:** The compressed summaries belong in the database, of course! We've already shown how we store conversations in SQLite. Now we simply add a new table for `compressed_memories`, with timestamps and session IDs. Then our agent memory survives server restarts and we can even analyze historical trends.

**Semantic compression:** Instead of just compressing temporally, we could also cluster thematically. All discussions about "security systems" in one block, "schedules" in another. This way memory becomes not only smaller, but also more structured.

**Adaptive compression:** Compress differently depending on importance. Critical decisions remain detailed, small talk gets aggressively shortened. The LLM could even evaluate what's important itself.

**Multi-level hierarchies:** Why only one level? Hour summaries become day summaries, which in turn become week summaries. Like our brain, which also works in different time levels.

**Error tolerance:** What happens when compression goes wrong? Backup strategies, validation of summaries, maybe even multiple LLMs for quality control.

The beautiful thing: All of this can be extended with what we built today. Our hierarchical memory is the foundation for really clever AI systems. Systems that don't "forget" what it was all about after a few hours.