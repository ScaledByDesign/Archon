#!/usr/bin/env python3
"""
Generate multiple funny stories using LiteLLM
"""

import requests
import json
import time

LITELLM_BASE_URL = "http://localhost:7010/v1"
LITELLM_API_KEY = "sk-wqn0xwq_vha4MVM2yzw"

def generate_stories():
    """Generate multiple funny stories"""
    
    # Different funny story prompts
    story_prompts = [
        {
            "title": "The Git Commit Disaster",
            "prompt": "Write a hilarious 150-word story about a developer who accidentally committed their diary entries instead of code, and now the entire team knows about their crush on the coffee machine."
        },
        {
            "title": "AI Gone Wrong",
            "prompt": "Write a funny 150-word story about a programmer who trained an AI to write code comments, but now it only writes passive-aggressive remarks about the developer's coding style."
        },
        {
            "title": "The Stack Overflow Hero",
            "prompt": "Write a comedic 150-word story about someone who becomes famous on Stack Overflow for always answering 'Have you tried turning it off and on again?' and it actually works 90% of the time."
        }
    ]
    
    # Alternate between models for variety
    models = ["zoi-coder", "gpt-4", "zoi-planner"]
    
    print("=" * 70)
    print("FUNNY PROGRAMMING STORIES COLLECTION")
    print("=" * 70)
    
    for i, story_data in enumerate(story_prompts, 1):
        model = models[i % len(models)]
        
        print(f"\n{'='*70}")
        print(f"Story #{i}: {story_data['title']}")
        print(f"Model: {model}")
        print("-" * 70)
        
        try:
            response = requests.post(
                f"{LITELLM_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {LITELLM_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a hilarious comedy writer who loves programming humor. Keep stories concise and punchy."},
                        {"role": "user", "content": story_data['prompt']}
                    ],
                    "max_tokens": 250,
                    "temperature": 0.85
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                story = data["choices"][0]["message"]["content"]
                
                # Clean up any thinking tags if present
                if "<think>" in story:
                    story = story.split("</think>")[-1].strip()
                
                print(story)
                print()
                
                if "usage" in data:
                    tokens = data["usage"]["total_tokens"]
                    print(f"[Tokens used: {tokens}]")
                
            else:
                print(f"[ERROR] Failed to generate story: {response.status_code}")
                
        except Exception as e:
            print(f"[ERROR] Exception: {e}")
        
        # Small delay between stories
        time.sleep(1)
    
    print("\n" + "=" * 70)
    print("THE END - Hope you enjoyed these programming comedy tales!")
    print("=" * 70)

if __name__ == "__main__":
    generate_stories()