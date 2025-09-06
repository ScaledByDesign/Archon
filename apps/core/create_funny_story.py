#!/usr/bin/env python3
"""
Create a funny story using LiteLLM proxy
"""

import requests
import json
import time

LITELLM_BASE_URL = "http://localhost:7010/v1"
LITELLM_API_KEY = "sk-wqn0xwq_vha4MVM2yzw"

def create_funny_story():
    """Create a funny story using LiteLLM"""
    print("Creating a funny story with LiteLLM...")
    print("=" * 50)
    
    # Story prompt
    story_prompt = """Write a short, funny story about a programmer who accidentally taught their smart home AI to only communicate in programming error messages. Make it hilarious and include actual error messages in the dialogue. Keep it under 300 words."""
    
    # Try different model names
    models_to_try = ["zoi-coder", "zoi-planner", "gpt-3.5-turbo", "gpt-4"]
    
    for model_name in models_to_try:
        print(f"\nAttempting with model: {model_name}")
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
                        {"role": "system", "content": "You are a creative and humorous storyteller."},
                        {"role": "user", "content": story_prompt}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.8
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                story = data["choices"][0]["message"]["content"]
                print(f"[SUCCESS] Story generated with {model_name}!")
                print("\n" + "=" * 50)
                print("THE FUNNY STORY:")
                print("=" * 50)
                print(story)
                print("=" * 50)
                
                if "usage" in data:
                    print(f"\nTokens used: {data['usage']}")
                
                return story
                
            else:
                print(f"[ERROR] Model {model_name} failed: {response.status_code}")
                error_msg = response.text[:200] if len(response.text) > 200 else response.text
                print(f"Error: {error_msg}")
                
                # If it's a 429 error, wait a bit before trying the next model
                if response.status_code == 429:
                    print("Waiting 5 seconds before trying next model...")
                    time.sleep(5)
                
        except Exception as e:
            print(f"[ERROR] Exception with {model_name}: {e}")
            continue
    
    print("\n" + "=" * 50)
    print("Unable to generate story with LiteLLM proxy.")
    print("All models returned errors.")
    print("=" * 50)
    return None

if __name__ == "__main__":
    story = create_funny_story()
    if not story:
        print("\nNo story was generated. Please check LiteLLM configuration.")