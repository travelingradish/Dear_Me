#!/usr/bin/env python3
"""Test script to verify prompt refactoring works correctly"""

import sys
import os
sys.path.append('/Users/wenjuanchen/daily_check_in_v2/backend')

from app.services.prompt_manager import PromptManager
from app.services.llm_service import OllamaLLMService
from app.services.guided_llm_service import GuidedLLMService

def test_prompt_manager():
    """Test PromptManager functionality"""
    print("🧪 Testing PromptManager...")
    
    pm = PromptManager()
    
    # Test conversation prompts
    conv_en = pm.get_prompt("conversation", "en")
    conv_zh = pm.get_prompt("conversation", "zh")
    
    print(f"✅ English conversation prompt: {len(conv_en)} characters")
    print(f"✅ Chinese conversation prompt: {len(conv_zh)} characters")
    
    # Test diary prompts
    diary_en = pm.get_prompt("diary", "en")
    diary_zh = pm.get_prompt("diary", "zh")
    
    print(f"✅ English diary prompt: {len(diary_en)} characters")
    print(f"✅ Chinese diary prompt: {len(diary_zh)} characters")
    
    # Test guided prompts
    guide_en = pm.get_prompt("guided", "en", "guide")
    guide_zh = pm.get_prompt("guided", "zh", "guide")
    composer_en = pm.get_prompt("guided", "en", "composer")
    composer_zh = pm.get_prompt("guided", "zh", "composer")
    
    print(f"✅ English guide prompt: {len(guide_en)} characters")
    print(f"✅ Chinese guide prompt: {len(guide_zh)} characters")
    print(f"✅ English composer prompt: {len(composer_en)} characters")
    print(f"✅ Chinese composer prompt: {len(composer_zh)} characters")
    
    # Test caching
    conv_en_cached = pm.get_prompt("conversation", "en")
    assert conv_en == conv_en_cached, "Caching failed"
    print("✅ Prompt caching works correctly")
    
    return True

def test_llm_service():
    """Test that OllamaLLMService works with PromptManager"""
    print("\n🧪 Testing OllamaLLMService with PromptManager...")
    
    try:
        service = OllamaLLMService()
        print("✅ OllamaLLMService initialized successfully")
        
        # Test that it can access prompts (without actually making LLM calls)
        # Just verify the service has the prompt manager
        assert hasattr(service, 'prompt_manager'), "LLM Service missing prompt_manager"
        print("✅ LLM Service has prompt_manager")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing LLM Service: {e}")
        return False

def test_guided_llm_service():
    """Test that GuidedLLMService works with PromptManager"""
    print("\n🧪 Testing GuidedLLMService with PromptManager...")
    
    try:
        service = GuidedLLMService()
        print("✅ GuidedLLMService initialized successfully")
        
        # Test that it can access prompts (without actually making LLM calls)
        assert hasattr(service, 'prompt_manager'), "Guided LLM Service missing prompt_manager"
        print("✅ Guided LLM Service has prompt_manager")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Guided LLM Service: {e}")
        return False

def test_error_handling():
    """Test error handling for invalid prompts"""
    print("\n🧪 Testing error handling...")
    
    pm = PromptManager()
    
    try:
        # Test invalid language
        pm.get_prompt("conversation", "invalid_lang")
        print("❌ Should have raised error for invalid language")
        return False
    except ValueError:
        print("✅ Correctly handles invalid language")
    
    try:
        # Test invalid mode
        pm.get_prompt("invalid_mode", "en")
        print("❌ Should have raised error for invalid mode")
        return False
    except (ValueError, FileNotFoundError):
        print("✅ Correctly handles invalid mode")
    
    try:
        # Test invalid prompt_type for guided mode
        pm.get_prompt("guided", "en", "invalid_type")
        print("❌ Should have raised error for invalid guided prompt type")
        return False
    except ValueError:
        print("✅ Correctly handles invalid guided prompt type")
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Testing Prompt Refactoring Implementation")
    print("=" * 60)
    
    tests = [
        test_prompt_manager,
        test_llm_service, 
        test_guided_llm_service,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test {test.__name__} failed")
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Prompt refactoring is working correctly.")
        return True
    else:
        print("💥 Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)