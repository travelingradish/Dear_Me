import requests
import json
import logging
import re
from typing import Dict, List, Optional, Union
from datetime import datetime
from prompt_manager import PromptManager

class OllamaLLMService:
    """Service for managing LLM interactions through Ollama"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ollama_url = "http://127.0.0.1:11434"
        self.prompt_manager = PromptManager()
        
        # Model configurations
        self.models = {
            'en': {
                'llama3.1:8b': {
                    'name': 'llama3.1:8b',
                    'display_name': 'Llama 3.1 (8B)',
                    'description': 'High-quality model for English conversations'
                },
                'qwen3:8b': {
                    'name': 'qwen3:8b',
                    'display_name': 'Qwen 3 (8B)',
                    'description': 'Specialized model, works for both English and Chinese'
                }
            },
            'zh': {
                'qwen3:8b': {
                    'name': 'qwen3:8b',
                    'display_name': 'Qwen 3 (8B)',
                    'description': 'Specialized Chinese language model'
                }
            }
        }
        
        # Default model selections
        self.default_models = {
            'en': 'llama3.1:8b',
            'zh': 'qwen3:8b'
        }
        
    
    def _filter_thinking_process(self, content: str) -> str:
        """Filter out thinking processes and internal reasoning from LLM response"""
        original_content = content
        
        # Remove <think>...</think> tags and content (complete blocks)
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove <thinking>...</thinking> tags and content (complete blocks)
        content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove incomplete thinking blocks (where response was cut off)
        content = re.sub(r'<think>.*$', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<thinking>.*$', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove Chinese reasoning patterns - more comprehensive
        content = re.sub(r'接下来，.*?。', '', content, flags=re.DOTALL)
        content = re.sub(r'用户.*?，所以我.*?。', '', content, flags=re.DOTALL)
        content = re.sub(r'我要.*?，.*?。', '', content, flags=re.DOTALL)
        content = re.sub(r'同时，要.*?。', '', content, flags=re.DOTALL)
        content = re.sub(r'另外，用户.*', '', content, flags=re.DOTALL)
        content = re.sub(r'这样.*?还能.*?。', '', content, flags=re.DOTALL)
        
        # Remove common Chinese reasoning starters
        content = re.sub(r'好的，.*?。我.*?。', '', content, flags=re.DOTALL)
        content = re.sub(r'我需要.*?。', '', content)
        content = re.sub(r'作为一个.*?，我应该.*?。', '', content, flags=re.DOTALL)
        content = re.sub(r'考虑到.*?，', '', content)
        
        # Remove incomplete sentences that might be reasoning
        lines = content.split('\n')
        filtered_lines = []
        for line in lines:
            line = line.strip()
            # Skip lines that look like internal reasoning
            if any(pattern in line for pattern in [
                '用户可能', '我要', '所以我', '这样能', '另外，', '同时，',
                '接下来，', '因此我', '我应该', '这时候'
            ]):
                continue
            if line:
                filtered_lines.append(line)
        
        content = '\n'.join(filtered_lines)
        
        # Clean up any remaining artifacts
        content = re.sub(r'\n+', '\n', content)  # Multiple newlines to single
        content = content.strip()
        
        # If filtering removed everything, return a fallback
        if not content or len(content) < 10:
            return "请继续分享，我很想了解更多。"
        
        return content
    
    def get_available_models(self, language: str) -> Dict:
        """Get available models for a specific language"""
        return self.models.get(language, {})
    
    def check_model_availability(self, model_name: str) -> bool:
        """Check if a specific model is available in Ollama"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models_data = response.json()
                model_names = [model['name'] for model in models_data['models']]
                return model_name in model_names
            return False
        except Exception as e:
            self.logger.error(f"Error checking model availability: {e}")
            return False
    
    def pull_model(self, model_name: str) -> bool:
        """Pull a model if it's not available"""
        try:
            self.logger.info(f"Pulling model: {model_name}")
            payload = {'name': model_name}
            response = requests.post(f"{self.ollama_url}/api/pull", json=payload)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Error pulling model {model_name}: {e}")
            return False
    
    def generate_conversation_response(self, 
                                    message: str, 
                                    conversation_history: List[Dict],
                                    language: str = 'en',
                                    model_name: Optional[str] = None,
                                    user_memories: Optional[List] = None) -> str:
        """Generate a conversation response using LLM"""
        
        if not model_name:
            model_name = self.default_models.get(language, 'llama3.1:8b')
        
        # Ensure model is available
        if not self.check_model_availability(model_name):
            if not self.pull_model(model_name):
                raise Exception(f"Model {model_name} not available and couldn't be pulled")
        
        # Build conversation context
        system_prompt = self.prompt_manager.get_prompt("conversation", language)
        
        # Add memory context if available
        if user_memories:
            from memory_service import MemoryService
            memory_service = MemoryService()
            memory_context = memory_service.format_memories_for_prompt(user_memories, language)
            if memory_context:
                system_prompt += f"\n\n{memory_context}\nUse this information naturally in conversation, but don't explicitly mention that you're recalling memories."
        
        # Format conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history (last 10 messages)
        for msg in conversation_history[-10:]:
            role = "user" if msg['type'] == 'user' else "assistant"
            messages.append({"role": role, "content": msg['message']})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        try:
            payload = {
                'model': model_name,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'num_predict': 500,  # Increased from 150 to prevent cutoffs
                    'num_ctx': 4096,     # Context window size
                    'stop': ['<think>', '<thinking>']  # Stop on thinking tags
                }
            }
            
            response = requests.post(f"{self.ollama_url}/api/chat", json=payload)
            
            if response.status_code == 200:
                response_data = response.json()
                content = response_data['message']['content'].strip()
                # Filter out thinking processes
                content = self._filter_thinking_process(content)
                return content
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
        except Exception as e:
            self.logger.error(f"Error generating conversation response: {e}")
            # Fallback response
            if language == 'zh':
                return "请继续分享，我很想了解更多。"
            else:
                return "Please continue sharing, I'd love to hear more."
    
    def generate_diary_entry(self, 
                           answers: Dict, 
                           conversation_history: List[Dict],
                           language: str = 'en',
                           tone: str = 'reflective',
                           model_name: Optional[str] = None) -> str:
        """Generate a diary entry using LLM"""
        
        if not model_name:
            model_name = self.default_models.get(language, 'llama3.1:8b')
        
        # Ensure model is available
        if not self.check_model_availability(model_name):
            if not self.pull_model(model_name):
                raise Exception(f"Model {model_name} not available and couldn't be pulled")
        
        # Build prompt with user's answers
        system_prompt = self.prompt_manager.get_prompt("diary", language)
        
        # Create context from answers and conversation
        today_date = datetime.now().strftime('%Y-%m-%d')
        
        if language == 'zh':
            context_prompt = f"""基于以下用户今天（{today_date}）的每日记录信息，写一篇个人日记条目。请仅使用提供的信息：

用户今天的回答：
"""
        else:
            context_prompt = f"""Based on the following user's daily check-in information from today ({today_date}), write a personal diary entry. Use ONLY the information provided below:

User's responses from today:
"""
        
        # Add answers to context - handle both structured and free-form data
        if answers:
            for key, value in answers.items():
                if value:
                    if language == 'zh':
                        labels = {
                            'mood': '心情',
                            'activities': '今日活动', 
                            'challenges': '面临挑战',
                            'gratitude': '感恩事物',
                            'progress': '取得进展',
                            'tomorrow': '明日计划',
                            'selfcare': '自我照顾'
                        }
                        # Handle response_X format from casual mode
                        if key.startswith('response_'):
                            label = f"回答 {key.split('_')[1]}"
                        else:
                            label = labels.get(key, key)
                    else:
                        labels = {
                            'mood': 'Mood',
                            'activities': 'Activities',
                            'challenges': 'Challenges', 
                            'gratitude': 'Gratitude',
                            'progress': 'Progress',
                            'tomorrow': 'Tomorrow',
                            'selfcare': 'Self-care'
                        }
                        # Handle response_X format from casual mode
                        if key.startswith('response_'):
                            label = f"Response {key.split('_')[1]}"
                        else:
                            label = labels.get(key, key.title())
                    
                    context_prompt += f"{label}: {value}\n"
        
        # Add conversation context if available
        if conversation_history:
            if language == 'zh':
                context_prompt += "\n今天的完整对话内容：\n"
            else:
                context_prompt += "\nComplete conversation from today:\n"
            
            # Add full conversation history to provide rich context
            for i, msg in enumerate(conversation_history[-10:], 1):  # Last 10 messages for context
                role = msg.get('type', 'user')
                message = msg.get('message', '')
                if message:
                    if role == 'user':
                        if language == 'zh':
                            context_prompt += f"我说：{message}\n"
                        else:
                            context_prompt += f"I said: {message}\n"
                    else:
                        if language == 'zh':
                            context_prompt += f"回应：{message}\n"
                        else:
                            context_prompt += f"Response: {message}\n"
        
        # Add dynamic length guidance based on conversation length
        conversation_length = len(conversation_history) if conversation_history else 0
        total_content_length = sum(len(str(v)) for v in answers.values() if v) if answers else 0
        if conversation_history:
            total_content_length += sum(len(msg.get('message', '')) for msg in conversation_history)
        
        if language == 'zh':
            if conversation_length <= 3 or total_content_length < 200:
                context_prompt += "\n长度指导：对话较简短，写一个简洁的日记条目（50-80字）。"
            elif conversation_length <= 8 or total_content_length < 600:
                context_prompt += "\n长度指导：对话内容适中，写一个平衡的日记条目（100-150字）。"
            else:
                context_prompt += "\n长度指导：对话内容丰富，写一个详细的日记条目（200-300字）。"
        else:
            if conversation_length <= 3 or total_content_length < 200:
                context_prompt += "\nLength guidance: Conversation is brief, write a concise diary entry (50-100 words)."
            elif conversation_length <= 8 or total_content_length < 600:
                context_prompt += "\nLength guidance: Conversation is moderate, write a balanced diary entry (150-200 words)."
            else:
                context_prompt += "\nLength guidance: Conversation is rich, write a comprehensive diary entry (250-400 words)."

        # Add tone instruction
        if language == 'zh':
            if tone == 'wind-down':
                context_prompt += "\n写作风格：夜晚放松、温暖反思的语调。"
            else:
                context_prompt += "\n写作风格：日间反思、积极向上的语调。"
            context_prompt += "\n\n重要提醒：只写关于今天的内容，不要编造细节或引用其他日期的事件。"
        else:
            if tone == 'wind-down':
                context_prompt += "\nTone: Evening wind-down, warm and reflective."
            else:
                context_prompt += "\nTone: Daytime reflection, positive and thoughtful."
            context_prompt += "\n\nIMPORTANT: Write only about today. Do not invent details or reference events from other dates."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context_prompt}
        ]
        
        try:
            # Dynamic token limit based on conversation richness
            if conversation_length <= 3 or total_content_length < 200:
                token_limit = 300  # For short diary entries
            elif conversation_length <= 8 or total_content_length < 600:
                token_limit = 500  # For medium diary entries
            else:
                token_limit = 800  # For comprehensive diary entries
            
            payload = {
                'model': model_name,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': 0.8,
                    'top_p': 0.9,
                    'num_predict': token_limit
                }
            }
            
            response = requests.post(f"{self.ollama_url}/api/chat", json=payload)
            
            if response.status_code == 200:
                response_data = response.json()
                content = response_data['message']['content'].strip()
                # Filter out thinking processes
                content = self._filter_thinking_process(content)
                return content
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
        except Exception as e:
            self.logger.error(f"Error generating diary entry: {e}")
            self.logger.error(f"Answers data: {answers}")
            self.logger.error(f"Conversation history length: {len(conversation_history) if conversation_history else 0}")
            # Fallback to template-based generation
            return self._fallback_diary_generation(answers, language, tone)
    
    def _fallback_diary_generation(self, answers: Dict, language: str, tone: str) -> str:
        """Fallback diary generation when LLM fails"""
        if language == 'zh':
            # Try to create a basic diary from answers if available
            if answers:
                content_parts = []
                for key, value in answers.items():
                    if value and str(value).strip():
                        if key == 'mood' or '心情' in str(key):
                            content_parts.append(f"我今天感觉{value}")
                        elif 'response_' in key:
                            content_parts.append(f"我分享了：{value}")
                        else:
                            content_parts.append(f"{value}")
                
                if content_parts:
                    return "。".join(content_parts) + "。这些都是我今天想要记录下来的。"
            
            return "今天我花时间反思了自己的感受和经历。通过记录这些想法，我能更好地理解自己的内心世界。"
        else:
            # Try to create a basic diary from answers if available
            if answers:
                content_parts = []
                for key, value in answers.items():
                    if value and str(value).strip():
                        if key == 'mood':
                            content_parts.append(f"I felt {value} today")
                        elif 'response_' in key:
                            content_parts.append(f"I shared: {value}")
                        else:
                            content_parts.append(f"{value}")
                
                if content_parts:
                    return ". ".join(content_parts) + ". These are the things I wanted to capture from today."
            
            return "Today I took time to reflect on my feelings and experiences. By recording these thoughts, I'm able to better understand my inner world."