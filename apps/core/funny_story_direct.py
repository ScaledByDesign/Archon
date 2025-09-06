#!/usr/bin/env python3
"""
Create a funny story using direct LLM Studio endpoint
Since LiteLLM proxy has routing issues, we'll use the working direct endpoints
"""

import requests
import json

def create_funny_story_direct():
    """Create funny story using direct LLM Studio endpoint"""
    print("Creating Funny Story with Direct LLM Studio Endpoint")
    print("=" * 60)
    
    # Use the RTX 3090 with the 30B model for better creativity
    endpoint = "http://192.168.8.241:1234/v1"
    model = "qwen/qwen3-coder-30b"
    
    print(f"Using: RTX 3090 - {model}")
    print("-" * 60)
    
    story_prompt = """Write a hilarious short story (under 300 words) about:

A programmer named Bob who accidentally taught his smart home AI to only communicate in programming error messages and HTTP status codes. 

Include scenarios like:
- Bob asking for the weather
- Trying to turn on the lights
- Ordering pizza
- The AI falling in love with his roomba

Make it absurdly funny with actual error messages and status codes!"""
    
    try:
        response = requests.post(
            f"{endpoint}/chat/completions",
            headers={
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a hilarious comedy writer who loves programming humor."},
                    {"role": "user", "content": story_prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.9
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            story = data["choices"][0]["message"]["content"]
            
            print("[SUCCESS] Story Generated!")
            print("\n" + "=" * 60)
            print("THE HILARIOUS TALE OF BOB AND HIS BROKEN AI")
            print("=" * 60 + "\n")
            print(story)
            print("\n" + "=" * 60)
            
            if "usage" in data:
                tokens = data["usage"]
                print(f"\nStats: {tokens['total_tokens']} tokens used")
                print(f"Model: {model} on RTX 3090")
            
            return story
        else:
            print(f"[ERROR] Failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
    
    return None

if __name__ == "__main__":
    story = create_funny_story_direct()
    if story:
        print("\n[INFO] Story successfully generated using direct LLM Studio endpoint!")