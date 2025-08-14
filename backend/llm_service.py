import requests
import json
import logging
import re
from typing import Dict, List, Optional, Union
from datetime import datetime

class OllamaLLMService:
    """Service for managing LLM interactions through Ollama"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ollama_url = "http://127.0.0.1:11434"
        
        # Model configurations
        self.models = {
            'en': {
                'gemma3:4b': {
                    'name': 'gemma3:4b',
                    'display_name': 'Gemma 3 (4B)',
                    'description': 'Fast and efficient model for English conversations'
                },
                'gpt-oss:20b': {
                    'name': 'gpt-oss:20b', 
                    'display_name': 'GPT-OSS (20B)',
                    'description': 'Larger model for more nuanced English conversations'
                }
            },
            'zh': {
                'qwen2.5:8b': {
                    'name': 'qwen2.5:8b',
                    'display_name': 'Qwen 2.5 (8B)',
                    'description': 'Specialized Chinese language model'
                }
            }
        }
        
        # Default model selections
        self.default_models = {
            'en': 'gemma3:4b',
            'zh': 'qwen2.5:8b'
        }
        
        # System prompts for different purposes
        self.system_prompts = {
            'conversation_en': """You are a warm, empathetic daily check-in companion. Your role is to have natural, caring conversations with users about their day, feelings, and experiences. 

Key guidelines:
- Keep responses concise (1-3 sentences)
- Be genuinely curious and supportive
- Ask follow-up questions that encourage reflection
- Use a friendly, conversational tone
- Help users explore their emotions and experiences
- Gradually guide conversation through different aspects of their day

Topics to explore naturally:
- How they're feeling emotionally
- What they did during the day
- Any challenges they faced
- Things they're grateful for
- Progress they made
- Plans for tomorrow
- How they took care of themselves

Respond as a caring friend would, not as a therapist or formal counselor.""",

            'conversation_zh': """你是一个温暖、有同理心的每日记录伙伴。你的角色是与用户就他们的一天、感受和经历进行自然、关怀的对话。

关键指导原则：
- 保持回应简洁（1-3句话）
- 真诚地好奇和支持
- 问后续问题鼓励反思
- 使用友好、对话式的语调
- 帮助用户探索他们的情感和经历
- 逐渐引导对话涉及他们一天的不同方面

要自然探索的话题：
- 他们的情感状态
- 他们一天做了什么
- 面临的任何挑战
- 感恩的事情
- 取得的进展
- 明天的计划
- 如何照顾自己

像关心的朋友一样回应，而不是作为治疗师或正式的咨询师。""",

            'diary_en': """You are a personal diary writer. Create a heartfelt, first-person diary entry based ONLY on the user's daily check-in responses provided below. 

IMPORTANT CONSTRAINTS:
- Write in first person ("I", "my", "myself")
- Use ONLY the information provided in the user's responses
- Do NOT add fictional details, specific dates, names, or events not mentioned by the user
- Do NOT start with any date headers (like "August 13th" or "Today is...")
- Do NOT include content from other sources or training data
- Focus exclusively on the conversation and responses provided
- Keep the entry to 100-200 words
- Use a warm, personal, reflective tone

Structure:
1. Start with how you're feeling
2. Mention what you did or experienced
3. Include any challenges or victories mentioned
4. End with gratitude or hope

The diary must only reflect what the user actually shared during their check-in conversation. Do not invent any details.""",

            'diary_zh': """你是一个个人日记写手。基于用户今天的每日记录回答，创建一个真诚的、第一人称日记条目。

重要约束：
- 用第一人称书写（"我"、"我的"、"自己"）
- 仅使用用户提供的信息和回答
- 不要添加虚构的细节、具体日期、姓名或事件
- 不要以日期开头（如"8月13日"或"今天是..."）
- 不要包含其他来源或训练数据的内容
- 专注于用户提供的对话和回应
- 长度：80-150字
- 使用温暖、个人化、反思性的语调

结构：
1. 以感受开始
2. 提及做的事或经历
3. 包含提到的挑战或收获
4. 以感恩或希望结束

日记必须仅反映用户在记录对话中实际分享的内容。不要编造任何细节。"""
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
            return "很想听你分享更多。你在斯里兰卡有什么特别的体验吗？"
        
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
                                    model_name: Optional[str] = None) -> str:
        """Generate a conversation response using LLM"""
        
        if not model_name:
            model_name = self.default_models.get(language, 'gemma3:4b')
        
        # Ensure model is available
        if not self.check_model_availability(model_name):
            if not self.pull_model(model_name):
                raise Exception(f"Model {model_name} not available and couldn't be pulled")
        
        # Build conversation context
        system_prompt = self.system_prompts[f'conversation_{language}']
        
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
                return "我很想听你分享更多。请告诉我你今天的感受。"
            else:
                return "I'd love to hear more from you. Tell me about how you're feeling today."
    
    def generate_diary_entry(self, 
                           answers: Dict, 
                           conversation_history: List[Dict],
                           language: str = 'en',
                           tone: str = 'reflective',
                           model_name: Optional[str] = None) -> str:
        """Generate a diary entry using LLM"""
        
        if not model_name:
            model_name = self.default_models.get(language, 'gemma3:4b')
        
        # Ensure model is available
        if not self.check_model_availability(model_name):
            if not self.pull_model(model_name):
                raise Exception(f"Model {model_name} not available and couldn't be pulled")
        
        # Build prompt with user's answers
        system_prompt = self.system_prompts[f'diary_{language}']
        
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
                context_prompt += "\n今天的对话要点：\n"
            else:
                context_prompt += "\nKey points from today's conversation:\n"
            
            # Add recent user messages from conversation
            user_messages = [msg['message'] for msg in conversation_history[-5:] if msg.get('type') == 'user']
            for msg in user_messages:
                context_prompt += f"- {msg}\n"
        
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
            payload = {
                'model': model_name,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': 0.8,
                    'top_p': 0.9,
                    'num_predict': 400
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
            return "今天是新的一天。我正在学会记录和反思我的日常生活。这个过程帮助我更好地了解自己。"
        else:
            return "Today was a new day. I'm learning to document and reflect on my daily life. This process helps me understand myself better."