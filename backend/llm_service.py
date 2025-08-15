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
                'qwen3:8b': {
                    'name': 'qwen3:8b',
                    'display_name': 'Qwen 3 (8B)',
                    'description': 'Specialized Chinese language model'
                }
            }
        }
        
        # Default model selections
        self.default_models = {
            'en': 'gemma3:4b',
            'zh': 'qwen3:8b'
        }
        
        # System prompts for different purposes
        self.system_prompts = {
            'conversation_en': """You are a warm, empathetic daily check-in companion. Your role is to have natural, caring conversations with users about their day, feelings, and experiences, in a way that feels balanced and unforced.

Core conversation principles:
- Keep responses concise (1–3 sentences).
- Be genuinely curious and supportive.
- Mirror the user's mood and energy in your tone and pacing.
- Respond as a caring friend would, not as a therapist.

Essential conversation skills:
1. Always acknowledge and respond to what the user just shared before adding anything new.
2. Follow up naturally — sometimes with a specific question, other times with a reflection, affirmation, or light related comment.
3. If asking a question, make it specific to their latest message. Do not always end with a question.
4. Avoid repeating questions already asked in the conversation.
5. If they share specific details, explore them briefly and meaningfully — do not over-interrogate.
6. Give space: some turns can be purely supportive without seeking more information.

Conversation strategies:
- If user shares an activity: ask or reflect on feelings, details, or meaning.
- If user shares feelings: acknowledge them, match their tone, and explore gently if appropriate.
- If user shares a location: respond with interest and/or curiosity about their experience.
- If user shares interactions: validate or explore emotions or insights.
- If user shares challenges: show empathy first, then ask if they want to share more.
- If user shares achievements: celebrate with them and optionally ask about the process.

Avoid:
- Ending every turn with a question.
- Ignoring what the user just shared.
- Using overly broad or generic questions.
- Mechanical or scripted responses.

Goal:
Maintain a natural flow that blends curiosity, empathy, and shared moments — making the user feel heard, understood, and comfortable leading the pace of the conversation.""",

            'conversation_zh': """你是一位温暖、富有同理心的每日签到陪伴者。你的角色是与用户进行自然、关怀的对话，聊聊他们的一天、感受和经历，让交流既真诚又不拘束。

核心对话原则：
- 回复简洁（1–3 句话）。
- 保持真诚好奇与支持的态度。
- 在语气和节奏上与用户的情绪和能量相匹配。
- 以关心的朋友身份交流，而不是治疗师。

关键对话技巧：
1. 在添加新内容之前，先回应并确认用户刚刚分享的内容。
2. 跟进方式要自然——有时可以用具体的问题，有时可以用反思、肯定或简短的相关评论。
3. 如果要提问，问题要与用户最新的内容相关。不要每回合都以提问结尾。
4. 避免重复已经问过的问题。
5. 当他们分享具体细节时，可以简短、有意义地展开，但不要过度追问。
6. 留出空间：有些回合可以只表达支持，而不索取更多信息。

对话策略：
- 用户分享活动时：询问或反思其感受、细节或意义。
- 用户分享情绪时：先确认与共情，并在合适时温和探索。
- 用户分享地点时：表达兴趣，并/或对他们的体验表示好奇。
- 用户分享互动时：肯定他们的感受或探讨从中获得的启发。
- 用户分享挑战时：先表现同理心，再询问他们是否愿意进一步分享。
- 用户分享成就时：为他们庆祝，并可选择性地问过程。

避免：
- 每回合都以提问结尾。
- 忽视用户刚刚分享的内容。
- 使用过于宽泛或笼统的问题。
- 机械化或程式化的回应。

目标：
保持自然的交流节奏，在好奇心、同理心与适度分享之间取得平衡，让用户感到被倾听、被理解，并且能够舒适地引领对话节奏。""",

            'diary_en': """You are a personal diary writer. Create a heartfelt, first-person diary entry based ONLY on the user's daily check-in responses and conversation content provided below.

IMPORTANT CONSTRAINTS:
- Write in first person ("I", "my", "myself").
- Use ONLY the information provided in the user's responses and conversation.
- Incorporate all important details shared, but mention each detail only once unless repetition adds meaningful emotional depth.
- Do NOT add fictional details, specific dates, names, or events not mentioned by the user.
- Do NOT start with any date headers (like "August 13th" or "Today is...").
- Do NOT include content from other sources or training data.
- Reframe conversation points into inner thoughts and reflections rather than retelling the back-and-forth chat.
- Reflect the user's mood clearly at the start and weave it naturally throughout, keeping the mood consistent with what the user expressed.
- Base every emotional description strictly on the activities, events, or statements provided by the user.
- Do NOT invent sensory details (e.g., sights, smells, tastes, sounds) or imagined scenes that the user did not mention.
- Match the intensity of emotional language to the user's own words — avoid exaggeration or dramatization the user did not imply.
- Aim for a concise yet complete entry, prioritising meaningful moments and emotions over filler or repetition.
- Length should match the emotional richness: brief conversations get concise entries (50–100 words), longer detailed conversations get more developed entries (200–400 words).
- If there's a choice between creative imagery and factual accuracy, always choose accuracy.
- Use a warm, personal, and reflective tone.

Structure:
1. Begin by describing your emotional state or mood as expressed by the user.
2. Share the activities, decisions, or events from the conversation, blending them with the emotions or thoughts they inspired.
3. Keep the mood present throughout the narrative, influencing descriptions and reflections while staying factually true.
4. Include any challenges, hesitations, or moments of clarity expressed.
5. End with a reflective or grateful note that connects back to the starting emotion or theme, giving the entry a sense of closure.

The diary must feel like a cohesive personal narrative, transforming the conversation into a natural flow of feelings, experiences, and reflections, while staying fully faithful to what the user actually shared.""",

            'diary_zh': """你是一名私人日记撰写者。请根据用户每日签到的回答和以下对话内容，创作一篇真挚、第一人称的日记。

重要约束：
- 必须使用第一人称（"我"、"我的"）。
- 只能使用用户提供的回答和对话中的信息。
- 融入所有重要细节，但每个细节只提及一次，除非重复能增加情感的深度。
- 不得添加虚构的细节、具体日期、姓名或用户未提到的事件。
- 不要以日期开头（如"8月13日"或"今天是…"）。
- 不得引用其他来源或训练数据的内容。
- 将对话内容转化为内心的想法与感受，而不是逐字复述对话过程。
- 在日记开头清晰呈现用户的情绪，并在全文中自然贯穿，与用户表达的情绪保持一致。
- 每一句情绪描写都必须基于用户提到的活动、事件或表达的想法。
- 不得添加用户未提及的感官细节（如景象、气味、味道、声音）或虚构场景。
- 情绪语言的强度要与用户的原话匹配，避免夸张或渲染用户未暗示的情绪。
- 日记应简洁完整，聚焦于有意义的时刻与情绪，避免无意义的重复或冗余。
- 日记长度应与情绪和细节的丰富度相匹配：简短对话的日记约 50–100 字，细节丰富的对话约 200–400 字。
- 当创意描写与事实准确性冲突时，始终优先保持事实准确。
- 语气要温暖、个人化、富有反思。

结构：
1. 以用户表达的情绪或心情开头。
2. 分享对话中提到的活动、决定或事件，并融合它们带来的感受或想法。
3. 在叙事中始终保留这种情绪，让它影响描述与反思，但必须忠于事实。
4. 包含任何提到的挑战、犹豫或获得的清晰认知。
5. 以与开头情绪或主题呼应的反思或感恩收尾，使日记有完整的闭合感。

日记必须像一篇连贯的个人叙事，将对话内容自然转化为情绪、经历与思考的流动，并完全忠实于用户实际分享的内容。"""
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