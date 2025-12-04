Welcome to Day 3! Once again, we are dealing with another cornerstone for the project: memory.

The problem: LLMs are stateless. How are agents supposed to know what has been discussed so far? This is crucial for this project (and for many other professional applications as well). The solution I am introducing here is a conversation memory.

The idea is that important—or all?—messages are stored in a history. For now, in this small example, I will store all messages. Next week, we will look at memory compression.

As in previous days, we start by establishing the connection to LM-Studio:

...


Then we begin by defining an agent with memory.

...

The agent is again initialized with a persona. You can read more about what that is in yesterday's post. Additionally, the conversation_history is initialized.

In the chat function, every user message (prompt) is appended to this history. The same applies to the response.
Before that, however, the messages are constructed. Here, the system message is combined with the history. This way, the LLM receives the entire message history every time and can respond more accurately.

Finally, there is a function that counts the characters and roughly converts them into tokens. I use the factor 4, since on average, 4 characters (including spaces) correspond to one token in English.

This value is a rough estimate and can vary depending on language, text type, and model used.

For short words (e.g., "the", "and"), a token may consist of 3–4 characters.
For longer words or words with special characters (e.g., "computer", "don't"), a token may consist of more than 4 characters.
For numbers or special characters, the value can also vary.
For a more accurate estimate, you can use the tokenizer of the model in use (e.g., GPT, BERT).

Finally, I initialize the agent and start a conversation.

...

I ask a few questions and also print out the answers.

My "conversation" also includes a test that checks whether the agent can remember previous messages. In other words, proof that the memory works.

Summary
You can see from the conversation that it is possible to refer back to previously provided information. This has many advantages, but also the disadvantage that the context keeps growing and may eventually no longer fit into the context window. This can certainly happen with our locally hosted LLM. As mentioned, more on this next week when we discuss memory compression.