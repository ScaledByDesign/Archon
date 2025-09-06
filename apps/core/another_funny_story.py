#!/usr/bin/env python3
"""
Generate another funny story using the working endpoint
"""

import requests
import json

def create_another_story():
    """Create another funny story with different prompt"""
    print("Generating Another Hilarious Story...")
    print("=" * 60)
    
    # Use RTX 5070 Ti this time for variety
    endpoint = "http://192.168.8.135:1234/v1"
    model = "qwen/qwen3-14b"
    
    print(f"Using: RTX 5070 Ti - {model}")
    print("-" * 60)
    
    story_prompt = """Write a super funny story (250 words max) about:

A software developer who discovers their code comments have become sentient and are now giving them life advice during code reviews. The comments are sassy, judgmental, and oddly accurate about the developer's personal life.

Include:
- Comments roasting their variable naming
- Comments about their dating life based on their commit history
- Comments that predict the future based on their coding patterns
- A plot twist ending

Make it hilarious and relatable to programmers!"""
    
    try:
        response = requests.post(
            f"{endpoint}/chat/completions",
            headers={
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a witty comedy writer who specializes in tech humor."},
                    {"role": "user", "content": story_prompt}
                ],
                "max_tokens": 400,
                "temperature": 0.85
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            story = data["choices"][0]["message"]["content"]
            
            print("[SUCCESS] Story Generated!")
            print("\n" + "=" * 60)
            print("THE SENTIENT CODE COMMENTS")
            print("=" * 60 + "\n")
            print(story)
            print("\n" + "=" * 60)
            
            if "usage" in data:
                print(f"\nGenerated on RTX 5070 Ti using {data['usage']['total_tokens']} tokens")
            
            return story
        else:
            print(f"[ERROR] Failed: {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
    
    return None

if __name__ == "__main__":
    create_another_story()