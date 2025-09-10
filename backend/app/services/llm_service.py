import requests
import json
import logging
import re
from typing import Dict, List, Optional, Union
from datetime import datetime
from app.services.prompt_manager import PromptManager

class OllamaLLMService:
    """Service for managing LLM interactions through Ollama"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ollama_url = "http://127.0.0.1:11434"
        self.prompt_manager = PromptManager()
        
        # Model configuration - using llama3.1:8b for all languages
        self.default_model = 'llama3.1:8b'
        
        self.models = {
            'llama3.1:8b': {
                'name': 'llama3.1:8b',
                'display_name': 'Llama 3.1 (8B)',
                'description': 'High-quality model for all languages'
            }
        }
        
        # Default model for all languages - for backward compatibility
        self.default_models = {
            'en': 'llama3.1:8b',
            'zh': 'llama3.1:8b'
        }
        
    def _filter_thinking_process(self, content: str, model_name: str = "llama3.1:8b", messages: List[Dict] = None) -> str:
        """Filter out thinking processes and internal reasoning from LLM response"""
        self.logger.debug(f"Filtering response for {model_name}: '{content[:100]}...'")
        
        # Remove thinking tags and content - llama3.1:8b should not produce these but being safe
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<think>.*$', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<thinking>.*$', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Clean up extra whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = content.strip()
        
        return content if content else "I'd be happy to help you with that. Could you tell me more?"
    
    def _get_age_appropriate_context(self, age: int, language: str) -> str:
        """Generate age-appropriate conversation context"""
        if language == 'zh':
            if age < 13:
                return "\n用户年龄提醒：用户是一名儿童（{age}岁）。请使用简单、友好、鼓励性的语言。避免复杂的概念，专注于学校、朋友、爱好和家庭等主题。保持积极向上的对话氛围。".format(age=age)
            elif age < 18:
                return "\n用户年龄提醒：用户是一名青少年（{age}岁）。可以讨论学校挑战、友谊、兴趣爱好、未来计划等青少年关心的话题。语言可以稍微成熟一些，但仍要保持支持和理解的态度。".format(age=age)
            elif age < 25:
                return "\n用户年龄提醒：用户是一名年轻成年人（{age}岁）。可以讨论大学生活、职业规划、人际关系、个人成长等话题。使用成熟但仍然充满活力的语调。".format(age=age)
            else:
                return "\n用户年龄提醒：用户是一名成年人（{age}岁）。可以进行深度的成熟对话，讨论职业、家庭、人生哲学、社会话题等。使用成熟、体贴的语调。".format(age=age)
        else:
            if age < 13:
                return f"\nUser age context: The user is a child ({age} years old). Please use simple, friendly, encouraging language. Avoid complex concepts, focus on topics like school, friends, hobbies, and family. Maintain a positive and uplifting conversational tone."
            elif age < 18:
                return f"\nUser age context: The user is a teenager ({age} years old). You can discuss school challenges, friendships, hobbies, future plans, and other topics that matter to teens. Language can be slightly more mature, but still maintain a supportive and understanding attitude."
            elif age < 25:
                return f"\nUser age context: The user is a young adult ({age} years old). You can discuss college life, career planning, relationships, personal growth, and other young adult concerns. Use a mature but still energetic tone."
            else:
                return f"\nUser age context: The user is an adult ({age} years old). You can engage in deep, mature conversations about career, family, life philosophy, social topics, and more. Use a mature, thoughtful tone."

    def get_available_models(self, language: str) -> List[Dict]:
        """Get available models for a specific language"""
        # Return just our single model for all languages
        return [self.models['llama3.1:8b']]
    
    def check_model_availability(self, model_name: str) -> bool:
        """Check if a specific model is available in Ollama"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models_data = response.json()
                available_models = [model['name'] for model in models_data.get('models', [])]
                return model_name in available_models
        except Exception as e:
            self.logger.error(f"Error checking model availability: {e}")
        return False

    def ensure_model_available(self, model_name: str) -> bool:
        """Ensure a model is available, pull it if not"""
        if self.check_model_availability(model_name):
            return True
        
        self.logger.info(f"Model {model_name} not available, attempting to pull...")
        try:
            payload = {'name': model_name}
            response = requests.post(f"{self.ollama_url}/api/pull", json=payload)
            if response.status_code == 200:
                self.logger.info(f"Successfully pulled model {model_name}")
                return True
        except Exception as e:
            self.logger.error(f"Error pulling model {model_name}: {e}")
        return False

    def send_message(self, message: str, conversation_history: List[Dict] = None, 
                     language: str = 'en', user_memories: List[str] = None, 
                     user_age: int = None, ai_character_name: str = "AI Assistant",
                     current_time: datetime = None) -> str:
        """Send a message to the LLM and get a response"""
        try:
            model_name = self.default_model
            
            if not self.ensure_model_available(model_name):
                raise Exception(f"Model {model_name} is not available and could not be pulled")

            # Build conversation context
            conversation_prompt = self.prompt_manager.get_prompt(
                mode="conversation",
                language=language
            ).replace("{ai_character_name}", ai_character_name)
            
            # Add current time context
            if not current_time:
                current_time = datetime.now()
            
            time_str = current_time.strftime("%Y-%m-%d %H:%M")
            day_of_week = current_time.strftime("%A")
            
            if language == 'zh':
                time_context = f"\n\n当前时间信息：{time_str}，{day_of_week}。请根据当前时间提供合适的回应，区分当前情况和历史模式。"
            else:
                time_context = f"\n\nCurrent time: {time_str}, {day_of_week}. Please respond appropriately to the current time and distinguish between current situations and historical patterns."
            
            conversation_prompt += time_context
            
            # Add age-appropriate context if age is provided
            if user_age:
                conversation_prompt += self._get_age_appropriate_context(user_age, language)
            
            # Add memory context if available
            if user_memories:
                if language == 'zh':
                    memory_intro = "\n\n关于用户的已知信息："
                    conversation_prompt += memory_intro + "\n".join([f"- {memory}" for memory in user_memories[-10:]])  # Last 10 memories
                else:
                    memory_intro = "\n\nWhat I know about the user:"
                    conversation_prompt += memory_intro + "\n".join([f"- {memory}" for memory in user_memories[-10:]])  # Last 10 memories
            
            # Build messages
            messages = [{"role": "system", "content": conversation_prompt}]
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history[-10:])  # Last 10 messages for context
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Make request to Ollama
            payload = {
                'model': model_name,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': 0.8,
                    'top_p': 0.9,
                    'num_predict': 300,
                    'num_ctx': 4096,
                    'repeat_penalty': 1.1
                }
            }
            
            response = requests.post(f"{self.ollama_url}/api/chat", json=payload)
            if response.status_code == 200:
                response_data = response.json()
                content = response_data['message']['content']
                
                # Filter thinking processes
                filtered_content = self._filter_thinking_process(content, model_name, messages)
                return filtered_content
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.logger.error(f"Error in send_message: {e}")
            if language == 'zh':
                return "抱歉，我遇到了一些技术问题。请稍后再试。"
            else:
                return "I'm sorry, I encountered a technical issue. Please try again."

    def generate_diary_entry(self, conversation_history: List[Dict], language: str = 'en', 
                           user_memories: List[str] = None, user_age: int = None, 
                           ai_character_name: str = "AI Assistant") -> str:
        """Generate a diary entry based on conversation history"""
        try:
            model_name = self.default_model
            
            if not self.ensure_model_available(model_name):
                raise Exception(f"Model {model_name} is not available and could not be pulled")

            # Load diary generation prompt
            diary_prompt = self.prompt_manager.get_prompt(
                mode="diary",
                language=language
            ).replace("{ai_character_name}", ai_character_name)
            
            # Add age-appropriate context if age is provided
            if user_age:
                diary_prompt += self._get_age_appropriate_context(user_age, language)
            
            # Add memory context if available
            if user_memories:
                if language == 'zh':
                    memory_intro = "\n\n关于用户的已知信息："
                    diary_prompt += memory_intro + "\n".join([f"- {memory}" for memory in user_memories[-10:]])
                else:
                    memory_intro = "\n\nWhat I know about the user:"
                    diary_prompt += memory_intro + "\n".join([f"- {memory}" for memory in user_memories[-10:]])
            
            # Build messages
            messages = [{"role": "system", "content": diary_prompt}]
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history[-15:])  # More context for diary generation
            
            # Add diary generation request
            if language == 'zh':
                messages.append({"role": "user", "content": "请基于我们刚才的对话，帮我生成一篇日记。"})
            else:
                messages.append({"role": "user", "content": "Please generate a diary entry based on our conversation."})
            
            # Make request
            payload = {
                'model': model_name,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'num_predict': 500,
                    'num_ctx': 4096,
                    'repeat_penalty': 1.05
                }
            }
            
            response = requests.post(f"{self.ollama_url}/api/chat", json=payload)
            if response.status_code == 200:
                response_data = response.json()
                content = response_data['message']['content']
                
                # Filter thinking processes
                filtered_content = self._filter_thinking_process(content, model_name, messages)
                return filtered_content
            else:
                self.logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                raise Exception(f"Failed to generate diary entry")
                
        except Exception as e:
            self.logger.error(f"Error generating diary entry: {e}")
            if language == 'zh':
                return "今天的对话让我思考了很多，我会继续反思这些想法。"
            else:
                return "Today's conversation gave me a lot to think about, and I'll continue reflecting on these thoughts."

    def generate_conversation_response(self, message: str, conversation_history: List[Dict] = None,
                                     language: str = 'en', model_name: str = None,
                                     user_memories: List[str] = None, character_name: str = "AI Assistant",
                                     user_age: int = None, current_time: datetime = None) -> str:
        """Generate a response for casual conversation mode with time and memory context"""
        return self.send_message(
            message=message,
            conversation_history=conversation_history,
            language=language,
            user_memories=user_memories,
            user_age=user_age,
            ai_character_name=character_name,
            current_time=current_time
        )

    def correct_grammar(self, text: str, language: str = 'en') -> str:
        """Correct grammar and spelling in text"""
        try:
            model_name = self.default_model
            
            if not self.ensure_model_available(model_name):
                raise Exception(f"Model {model_name} is not available")

            # Load grammar correction prompt
            grammar_prompt = self.prompt_manager.get_prompt(
                mode="grammar",
                language=language
            )
            
            messages = [
                {"role": "system", "content": grammar_prompt},
                {"role": "user", "content": text}
            ]
            
            payload = {
                'model': model_name,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': 0.3,  # Lower temperature for grammar correction
                    'top_p': 0.8,
                    'num_predict': 800,
                    'num_ctx': 2048,
                    'repeat_penalty': 1.0
                }
            }
            
            response = requests.post(f"{self.ollama_url}/api/chat", json=payload)
            if response.status_code == 200:
                response_data = response.json()
                content = response_data['message']['content']
                
                # Filter thinking processes
                filtered_content = self._filter_thinking_process(content, model_name, messages)
                return filtered_content
            else:
                self.logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return text  # Return original if correction fails
                
        except Exception as e:
            self.logger.error(f"Error correcting grammar: {e}")
            return text

    def improve_writing(self, text: str, improvement_type: str, language: str = 'en') -> str:
        """Improve writing with specified improvement type"""
        try:
            model_name = self.default_model
            
            if not self.ensure_model_available(model_name):
                raise Exception(f"Model {model_name} is not available")

            # Load writing improvement prompt
            improvement_prompt = self.prompt_manager.get_prompt(
                mode="writing",
                language=language,
                prompt_type=improvement_type
            )
            
            messages = [
                {"role": "system", "content": improvement_prompt},
                {"role": "user", "content": text}
            ]
            
            payload = {
                'model': model_name,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': 0.6,
                    'top_p': 0.85,
                    'num_predict': 800,
                    'num_ctx': 2048,
                    'repeat_penalty': 1.05
                }
            }
            
            response = requests.post(f"{self.ollama_url}/api/chat", json=payload)
            if response.status_code == 200:
                response_data = response.json()
                content = response_data['message']['content']
                
                # Filter thinking processes  
                filtered_content = self._filter_thinking_process(content, model_name, messages)
                return filtered_content
            else:
                self.logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return text
                
        except Exception as e:
            self.logger.error(f"Error improving writing: {e}")
            return text