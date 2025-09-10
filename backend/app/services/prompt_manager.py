import logging
from typing import Dict, Optional
from pathlib import Path

class PromptManager:
    """Manages prompt loading and caching for different languages and modes"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        
        self._cache: Dict[str, str] = {}
        
        # Validate prompts directory exists
        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {self.prompts_dir}")
    
    def _get_cache_key(self, mode: str, prompt_type: str, language: str) -> str:
        """Generate cache key for prompt"""
        return f"{mode}_{prompt_type}_{language}"
    
    def _load_prompt_from_file(self, mode: str, prompt_type: str, language: str) -> str:
        """Load prompt from file system"""
        
        # Map prompt types to file names
        if mode == "guided":
            if prompt_type == "guide":
                filename = f"guide_{language}.txt"
            elif prompt_type == "composer":
                filename = f"composer_{language}.txt"
            else:
                raise ValueError(f"Unknown guided prompt type: {prompt_type}")
        elif mode in ["conversation", "diary"]:
            filename = f"{language}.txt"
        else:
            raise ValueError(f"Unknown mode: {mode}")
        
        file_path = self.prompts_dir / mode / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                raise ValueError(f"Empty prompt file: {file_path}")
            
            return content
            
        except Exception as e:
            self.logger.error(f"Error loading prompt from {file_path}: {e}")
            raise
    
    def get_prompt(self, mode: str, language: str, prompt_type: Optional[str] = None) -> str:
        """
        Get prompt for specified mode, language, and optional prompt type
        
        Args:
            mode: "conversation", "diary", or "guided"
            language: "en" or "zh"
            prompt_type: For guided mode: "guide" or "composer". Not used for other modes.
        
        Returns:
            Prompt text
        """
        
        # Validate inputs
        if language not in ["en", "zh"]:
            raise ValueError(f"Unsupported language: {language}")
        
        if mode == "guided" and prompt_type not in ["guide", "composer"]:
            raise ValueError(f"For guided mode, prompt_type must be 'guide' or 'composer', got: {prompt_type}")
        
        if mode in ["conversation", "diary"] and prompt_type is not None:
            self.logger.warning(f"prompt_type '{prompt_type}' ignored for mode '{mode}'")
            prompt_type = None
        
        # Generate cache key
        cache_key = self._get_cache_key(mode, prompt_type or "default", language)
        
        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Load from file
        try:
            prompt = self._load_prompt_from_file(mode, prompt_type, language)
            
            # Cache the result
            self._cache[cache_key] = prompt
            
            self.logger.debug(f"Loaded prompt: {cache_key}")
            return prompt
            
        except Exception as e:
            self.logger.error(f"Failed to load prompt for {cache_key}: {e}")
            return self._get_fallback_prompt(mode, language, prompt_type)
    
    def _get_fallback_prompt(self, mode: str, language: str, prompt_type: Optional[str]) -> str:
        """Provide fallback prompts when file loading fails for valid modes only"""
        
        # Only provide fallbacks for valid modes
        valid_modes = ["conversation", "diary", "guided"]
        if mode not in valid_modes:
            raise ValueError(f"Unknown mode: {mode}")
        
        if language == "zh":
            if mode == "conversation":
                return "你是一位温暖、富有同理心的陪伴者。请与用户进行自然、关怀的对话。"
            elif mode == "diary":
                return "你是一名私人日记撰写者。请根据用户的回答创作一篇真挚的第一人称日记。"
            elif mode == "guided":
                if prompt_type == "guide":
                    return "你是一位温暖的陪伴者，帮助用户回顾他们的一天。请进行自然、关怀的对话。"
                else:  # composer
                    return "你是一个日记写手，请从用户的数据中创建温暖的第一人称日记条目。"
        else:  # English
            if mode == "conversation":
                return "You are a warm, empathetic daily check-in companion. Have natural, caring conversations with users."
            elif mode == "diary":
                return "You are a personal diary writer. Create a heartfelt, first-person diary entry based on the user's responses."
            elif mode == "guided":
                if prompt_type == "guide":
                    return "You are a warm companion helping the user reflect on their day. Guide a natural, caring conversation."
                else:  # composer
                    return "You are a diary writer creating warm, first-person diary entries from user data."
        
        return "Please have a natural conversation with the user."
    
    def clear_cache(self):
        """Clear the prompt cache"""
        self._cache.clear()
        self.logger.info("Prompt cache cleared")
    
    def reload_prompt(self, mode: str, language: str, prompt_type: Optional[str] = None):
        """Reload a specific prompt from file, bypassing cache"""
        cache_key = self._get_cache_key(mode, prompt_type or "default", language)
        
        # Remove from cache if exists
        if cache_key in self._cache:
            del self._cache[cache_key]
        
        # Load fresh from file
        return self.get_prompt(mode, language, prompt_type)
    
    def get_available_prompts(self) -> Dict[str, Dict[str, list]]:
        """Get list of available prompts organized by mode and language"""
        available = {}
        
        for mode_dir in self.prompts_dir.iterdir():
            if mode_dir.is_dir():
                mode = mode_dir.name
                available[mode] = {}
                
                for prompt_file in mode_dir.glob("*.txt"):
                    filename = prompt_file.stem
                    
                    if mode == "guided":
                        if "_" in filename:
                            prompt_type, lang = filename.split("_", 1)
                            if lang not in available[mode]:
                                available[mode][lang] = []
                            available[mode][lang].append(prompt_type)
                    else:
                        lang = filename
                        available[mode][lang] = ["default"]
        
        return available