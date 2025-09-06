#!/usr/bin/env python3
"""
Try creating story with exact model names from config
"""

import requests
import json
import time

LITELLM_BASE_URL = "http://localhost:7010/v1"
LITELLM_API_KEY = "sk-wqn0xwq_vha4MVM2yzw"

def create_story_exact():
    """Try with exact model configurations"""
    print("Attempting story generation with exact model configurations...")
    print("=" * 50)
    
    story_prompt = """Write a short, funny story about a developer who accidentally deployed their shopping list to production instead of their code. Make it hilarious! Keep it under 200 words."""
    
    # Try with the exact underlying model names
    exact_models = [
        ("openai/qwen/qwen3-14b", "Direct Qwen3-14B"),
        ("openai/qwen/qwen3-coder-30b", "Direct Qwen3-Coder-30B"),
        ("zoi-coder", "Zoi Coder Alias"),
        ("gpt-3.5-turbo", "GPT-3.5 Alias")
    ]
    
    for model_name, description in exact_models:
        print(f"\nTrying: {description} ({model_name})")
        print("-" * 30)
        
        try:
            response = requests.post(
                f"{LITELLM_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {LITELLM_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "user", "content": story_prompt}
                    ],
                    "max_tokens": 300,
                    "temperature": 0.7,
                    "stream": False
                },
                timeout=30
            )
            
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                story = data["choices"][0]["message"]["content"]
                print("[SUCCESS] Story generated!")
                print("\n" + "=" * 50)
                print("FUNNY STORY:")
                print("=" * 50)
                print(story)
                print("=" * 50)
                return story
            else:
                print(f"Failed: {response.text[:100]}...")
                
        except Exception as e:
            print(f"Exception: {e}")
        
        time.sleep(2)  # Brief pause between attempts
    
    print("\nAll attempts failed.")
    return None

if __name__ == "__main__":
    create_story_exact()