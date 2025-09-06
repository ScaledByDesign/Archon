#!/usr/bin/env python3
"""
Generate a clean funny story
"""

import requests
import json

def generate_clean_story():
    """Generate a clean funny story"""
    print("Generating Clean Funny Story...")
    print("=" * 60)
    
    # Use RTX 3090 for best results
    endpoint = "http://192.168.8.241:1234/v1"
    model = "qwen/qwen3-coder-30b"
    
    story_prompt = """Write a hilarious 200-word story about a programmer who accidentally swapped their Zoom background with their code editor during an important client presentation. The code contained embarrassing variable names and comments. Make it funny!"""
    
    try:
        response = requests.post(
            f"{endpoint}/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "user", "content": story_prompt}
                ],
                "max_tokens": 300,
                "temperature": 0.8
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            story = data["choices"][0]["message"]["content"]
            
            print("\n" + "=" * 60)
            print("ZOOM DISASTER: A PROGRAMMER'S TALE")
            print("=" * 60 + "\n")
            print(story)
            print("\n" + "=" * 60)
            
            return story
            
    except Exception as e:
        print(f"Error: {e}")
    
    return None

if __name__ == "__main__":
    generate_clean_story()