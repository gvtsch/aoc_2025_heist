# My advent of Code 2025
Many of you probably know Advent of Code. It’s an interesting and fun project that I’ve participated in several times in the past. But this year, I want to create my own Advent of Code. Over the past weeks, months, and years, I’ve explored various frameworks, tools, and concepts in the field of artificial intelligence—some in large projects (like FAISS and LangChain in a professional RAG system), others just in simple examples (like MCP), and some I haven’t used at all yet (for example Snowflake).

In this project, I want to bring some of these concepts together. Every day, I’ll implement a small feature, and at the end, combine everything into a working project. Hopefully ...

## The Idea

A multi-agent system with four agents planning a bank heist together. One of them will secretly sabotage the plan.

## The Building Blocks

### Local LLMs (LM Studio)

No cloud dependency, no API costs, full data control. Important for real business use cases.

### OAuth 2.0 & Security

Not every agent can see everything. Only the hacker gets access to building plans. Role-based access control for AI.

### Microservices

One service for memory, one for simulation, one for analysis. Clean separation of concerns with Docker.

### Model Context Protocol (MCP)

A “new” standard from Anthropic. Connect tools to LLMs in a unified way instead of building for each provider separately.

### Memory Management

LLMs have context limits. Old conversations need to be compressed—hierarchical memory like humans.

### Push Analysis

Who influences whom in the team? Causality instead of correlation. Apply graph theory to AI conversations. And in the end: Can I algorithmically identify the saboteur?

## The Challenge

How do agents communicate effectively with information asymmetry? How do you orchestrate turn-based coordination across multiple services? How do you engineer prompts for subtle deception? How do you measure influence between AIs? How do you integrate all of this?

The interesting part isn’t the individual technology, but how they work together. And to make this happen, I’ve given myself 24 days. One small thing each day, one feature or learning every day. And everything is public.
