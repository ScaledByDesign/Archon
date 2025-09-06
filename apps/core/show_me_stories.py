#!/usr/bin/env python3
"""
Show me the funny stories!
"""

import requests
import json

LITELLM_BASE_URL = "http://localhost:7010/v1"
LITELLM_API_KEY = "sk-wqn0xwq_vha4MVM2yzw"

def show_stories():
    """Generate and display funny stories"""
    
    stories = [
        {
            "title": "The Bug That Became a Feature",
            "prompt": "Write a 100-word funny story about a developer whose bug became the most popular feature of their app - a button that randomly plays the Windows XP shutdown sound during video calls.",
            "model": "zoi-coder"
        },
        {
            "title": "Coffee Machine Romance",
            "prompt": "Write a 100-word hilarious story about a programmer who wrote a love letter to the office coffee machine in JavaScript, but accidentally deployed it to the company website.",
            "model": "gpt-4"
        },
        {
            "title": "Rubber Duck Rebellion",
            "prompt": "Write a 100-word comedy about rubber ducks organizing a strike because programmers keep explaining boring bugs to them instead of interesting problems.",
            "model": "zoi-planner"
        },
        {
            "title": "The Legacy Code Horror",
            "prompt": "Write a 100-word funny horror story about a developer who discovers their own code from 5 years ago with a comment that says 'DO NOT TOUCH - I don't remember what this does but everything breaks without it.'",
            "model": "zoi-coder"
        }
    ]
    
    print("\n" + "=" * 70)
    print("                    FUNNY PROGRAMMING STORIES")
    print("=" * 70)
    
    for story_data in stories:
        print(f"\n{story_data['title']}")
        print("-" * 50)
        
        try:
            response = requests.post(
                f"{LITELLM_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {LITELLM_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": story_data['model'],
                    "messages": [
                        {"role": "user", "content": story_data['prompt']}
                    ],
                    "max_tokens": 200,
                    "temperature": 0.8
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                story = data["choices"][0]["message"]["content"]
                
                # Remove any thinking tags
                if "<think>" in story:
                    story = story.split("</think>")[-1].strip()
                if not story or len(story) < 10:
                    story = data["choices"][0]["message"]["content"]
                
                print(story)
                
            else:
                # Fallback to working model if one fails
                if story_data['model'] == 'gpt-4':
                    story_data['model'] = 'zoi-planner'
                    response = requests.post(
                        f"{LITELLM_BASE_URL}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {LITELLM_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": story_data['model'],
                            "messages": [
                                {"role": "user", "content": story_data['prompt']}
                            ],
                            "max_tokens": 200,
                            "temperature": 0.8
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        story = data["choices"][0]["message"]["content"]
                        print(story)
                    else:
                        print(f"[Story generation failed]")
                
        except Exception as e:
            print(f"[Error: {e}]")
    
    print("\n" + "=" * 70)
    print("                         THE END")
    print("=" * 70)

if __name__ == "__main__":
    show_stories()