#!/usr/bin/env python3
"""
Final funny stories showcase
"""

import requests
import json

LITELLM_BASE_URL = "http://localhost:7010/v1"
LITELLM_API_KEY = "sk-wqn0xwq_vha4MVM2yzw"

def final_stories():
    """Generate final set of funny stories"""
    
    print("\n" + "=" * 70)
    print("         HILARIOUS PROGRAMMING STORIES - FINAL EDITION")
    print("=" * 70)
    
    # Story 1
    print("\n[STORY 1] The Merge Conflict of Love")
    print("-" * 50)
    
    response = requests.post(
        f"{LITELLM_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {LITELLM_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "zoi-coder",
            "messages": [
                {"role": "user", "content": "Write a 100-word funny story about two developers who fell in love while resolving a massive merge conflict that had 500 conflicts in a single file."}
            ],
            "max_tokens": 200,
            "temperature": 0.8
        },
        timeout=30
    )
    
    if response.status_code == 200:
        story = response.json()["choices"][0]["message"]["content"]
        # Clean up thinking tags
        if "<think>" in story:
            parts = story.split("</think>")
            if len(parts) > 1 and parts[1].strip():
                story = parts[1].strip()
            else:
                story = story.replace("<think>", "").replace("</think>", "")
        print(story)
    
    # Story 2
    print("\n[STORY 2] The AI Assistant's Revenge")
    print("-" * 50)
    
    response = requests.post(
        f"{LITELLM_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {LITELLM_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "zoi-planner",
            "messages": [
                {"role": "user", "content": "Write a 100-word funny story about an AI coding assistant that starts inserting rickroll links in all the documentation because it's tired of answering the same questions."}
            ],
            "max_tokens": 200,
            "temperature": 0.8
        },
        timeout=30
    )
    
    if response.status_code == 200:
        story = response.json()["choices"][0]["message"]["content"]
        print(story)
    
    # Story 3
    print("\n[STORY 3] The Production Incident")
    print("-" * 50)
    
    response = requests.post(
        f"{LITELLM_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {LITELLM_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4",
            "messages": [
                {"role": "user", "content": "Write a 100-word funny story about a developer who fixed a production bug by adding a comment that says 'magic happens here' and nobody knows why it works."}
            ],
            "max_tokens": 200,
            "temperature": 0.8
        },
        timeout=30
    )
    
    if response.status_code == 200:
        story = response.json()["choices"][0]["message"]["content"]
        print(story)
    
    print("\n" + "=" * 70)
    print("THE END - Thanks for reading!")
    print("Generated using LiteLLM with Zoi models")
    print("=" * 70)

if __name__ == "__main__":
    final_stories()