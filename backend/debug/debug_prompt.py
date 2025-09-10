#!/usr/bin/env python3
"""
Debug prompt loading to see what's actually being used.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prompt_manager import PromptManager

def debug_prompts():
    """Debug what prompts are being loaded"""
    print("🔍 Debugging Prompt Loading...")
    
    prompt_manager = PromptManager()
    
    try:
        # Test English prompt loading
        en_prompt = prompt_manager.get_prompt("guided", "en", "guide")
        print(f"English prompt loaded successfully:")
        print(f"Length: {len(en_prompt)} characters")
        print(f"First 200 characters:")
        print(en_prompt[:200])
        print("...")
        print(f"Last 200 characters:")
        print(en_prompt[-200:])
        
        # Test Chinese prompt loading
        zh_prompt = prompt_manager.get_prompt("guided", "zh", "guide")
        print(f"\nChinese prompt loaded successfully:")
        print(f"Length: {len(zh_prompt)} characters")
        print(f"First 200 characters:")
        print(zh_prompt[:200])
        
        # Check if there's Chinese text in the English prompt
        chinese_chars = any('\u4e00' <= char <= '\u9fff' for char in en_prompt)
        print(f"\nChinese characters in English prompt: {chinese_chars}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading prompts: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_prompts()