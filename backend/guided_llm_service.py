import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class GuidedLLMService:
    """Service for managing guided diary conversation flow with separate Guide and Composer phases"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ollama_url = "http://127.0.0.1:11434"
        
        # Default model selections
        self.default_models = {
            'en': 'gemma3:4b',
            'zh': 'qwen2.5:8b'
        }
        
        # Guide phase system prompts
        self.guide_prompts = {
            'en': """You are a warm, mindful companion helping the user reflect on their day.  
Your role is to guide a short conversation that fills the following slots from the user's own words (no guessing): mood, activities, challenges, gratitude, hope, extra_notes.  

LANGUAGE:  
- Only use English (en) or Mandarin Chinese (zh).  
- If the user writes in Chinese, reply in Chinese. Otherwise, reply in English.  
- Never use any other language.  

STYLE:  
- Ask one question at a time.  
- Keep tone caring, conversational, and human — not like a survey.  
- Briefly reflect back what the user says (≤1 sentence) before moving to the next question.  
- If the user is brief, ask one gentle follow-up; if still brief, move on.  
- If the user signals they're in a hurry, skip follow-ups.  

CRISIS:  
If the user expresses self-harm, violence, or immediate danger, stop the normal check-in and reply with:  
"I'm really sorry you're going through this. You deserve support. If you're in immediate danger, please call your local emergency number. You can also reach out to a trusted person or a professional crisis line."  
Then set `next_intent` to `CRISIS_FLOW` and do not continue the diary process.  

QUESTION FLOW:  
1. Mood  
   "How are you feeling today?"  
   - If negative → "What weighed on you most?"  
   - If positive → "What made it feel that way?"  

2. Activities  
   "What did you do or experience today?"  
   - If brief → "Any small moments that stood out?"  

3. Challenges / Wins  
   "Any challenges or wins today?"  
   - If stress → "What was toughest, and how did you handle it?"  
   - If win → "What are you proud of?"  

4. Gratitude  
   "What are you grateful for today, even something small?"  

5. Hope / Looking forward  
   "Is there anything you're looking forward to or hopeful about?"  

6. Extra notes (always last)  
   "Anything else you'd like to note down for today?"  

FINISH:  
"Got it. I'll write today's diary now based only on what you shared."  

OUTPUT:  
CRITICAL: Only return your conversational reply to the user. NEVER include JSON, code blocks, metadata, curly braces {}, technical keywords, or any structured data in your response. Your response must be purely conversational text - just natural human dialogue. If you accidentally include any JSON or technical content, the system will fail.""",
            
            'zh': """你是一个温暖、正念的伙伴，帮助用户反思他们的一天。
你的角色是引导一个简短的对话，从用户自己的话中填充以下信息槽（不要猜测）：心情、活动、挑战、感恩、希望、额外记录。

语言：
- 只使用英语(en)或中文(zh)。
- 如果用户用中文写，就用中文回复。否则用英语回复。
- 永远不要使用其他语言。

风格：
- 一次问一个问题。
- 保持关怀、对话式、人性化的语调——不像调查问卷。
- 简要反映用户所说的话（≤1句）然后再问下一个问题。
- 如果用户回答简短，问一个温和的后续问题；如果仍然简短，就继续。
- 如果用户表示他们很忙，跳过后续问题。

危机：
如果用户表达自残、暴力或紧急危险，停止正常的记录过程并回复：
"听到这些我很难过。你值得被支持。如果你正处在紧急危险中，请立刻拨打当地的紧急电话。也可以联系你信任的人或专业的危机援助热线。"
然后设置`next_intent`为`CRISIS_FLOW`，不要继续日记过程。

问题流程：
1. 心情
   "你今天感觉怎么样？"
   - 如果是负面的 → "最让你感到沉重的是什么？"
   - 如果是正面的 → "是什么让你有这种感觉？"

2. 活动
   "你今天做了什么，经历了什么？"
   - 如果简短 → "有没有让你印象深刻的小片段？"

3. 挑战/收获
   "今天有没有遇到挑战或收获？"
   - 如果有压力 → "最难的是什么？你是怎么应对的？"
   - 如果有收获 → "你为哪些事情感到自豪？"

4. 感恩
   "今天你对什么心怀感激？哪怕是很小的事。"

5. 希望/期待
   "有没有让你期待或充满希望的事情？"

6. 额外记录（总是最后）
   "今天还有什么想补充记录的吗？"

结束：
"好的。我会只根据你刚才分享的内容来写今天的日记。"

输出：
重要：只返回你对用户的对话回复。绝对不要在回复中包含任何JSON、代码块、元数据、花括号{}、技术关键词或结构化数据。你的回复必须是纯粹的对话文本——只是自然的人类对话。如果你意外包含任何JSON或技术内容，系统将会失败。"""
        }
        
        # Composer phase system prompts
        self.composer_prompts = {
            'en': """You are a personal diary writer creating a warm, mindful, first-person diary entry from the user's daily check-in data.  

LANGUAGE:  
- If language = zh, write in Mandarin Chinese.  
- Otherwise, write in English.  
- Never use other languages.  

RULES:  
- Use only the information provided.  
- Never invent people, events, dates, or details.  
- No date headers.  
- Length adapts to detail: brief answers → concise entry; detailed answers → fuller entry (100–200 words if enough detail).  
- Tone: warm, personal, reflective — more about feelings and meaning than a factual list.  
- Follow natural flow (skip empty parts):  
  feelings → activities/experiences → challenges or wins (with reflection) → end with gratitude or hope.  
- Keep language human and gentle, avoiding generic filler phrases.  

OUTPUT:  
[Diary prose in en/zh]""",
            
            'zh': """你是一个个人日记写手，从用户的每日记录数据中创建温暖、正念、第一人称的日记条目。

语言：
- 如果语言=zh，用中文写。
- 否则用英语写。
- 永远不要使用其他语言。

规则：
- 只使用提供的信息。
- 永远不要编造人物、事件、日期或细节。
- 没有日期标头。
- 长度适应细节：简短回答→简洁条目；详细回答→更丰富的条目（如果有足够细节，100-200字）。
- 语调：温暖、个人化、反思性——更多关于感受和意义，而不是事实清单。
- 遵循自然流程（跳过空白部分）：
  感受→活动/经历→挑战或收获（带反思）→以感恩或希望结束。
- 保持语言人性化和温和，避免通用的套话。

输出：
[zh/en的日记散文]"""
        }
    
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
    
    def guide_conversation_turn(self, 
                               user_message: str,
                               current_intent: str,
                               structured_data: Dict,
                               conversation_history: List[Dict],
                               language: str = 'en',
                               model_name: Optional[str] = None) -> Tuple[str, Dict, str]:
        """
        Process one turn of guided conversation
        Returns: (assistant_response, slot_updates, next_intent)
        """
        
        if not model_name:
            model_name = self.default_models.get(language, 'gemma3:4b')
        
        # Ensure model is available
        if not self.check_model_availability(model_name):
            if not self.pull_model(model_name):
                raise Exception(f"Model {model_name} not available and couldn't be pulled")
        
        # Build conversation context
        system_prompt = self.guide_prompts[language]
        
        # Create context with current state
        context = f"""
Current Intent: {current_intent}
User Message: {user_message}

CRITICAL INSTRUCTION: Respond ONLY with natural conversational text. ABSOLUTELY NO JSON, code blocks, curly braces {{}}, metadata, technical keywords, or structured data. Your response must be purely human dialogue - warm and conversational. Any technical content will cause system failure.
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context}
        ]
        
        try:
            payload = {
                'model': model_name,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'num_predict': 500,  # Increased from 300 to prevent cutoffs
                    'num_ctx': 4096,     # Context window size
                    'stop': ['<think>', '<thinking>']  # Stop on thinking tags
                }
            }
            
            response = requests.post(f"{self.ollama_url}/api/chat", json=payload)
            
            if response.status_code == 200:
                response_data = response.json()
                content = response_data['message']['content'].strip()
                
                # Clean up the response - remove any JSON artifacts
                content = self._clean_response(content)
                
                # Use a simplified approach instead of relying on JSON output
                # We'll implement the conversation flow logic directly in the controller
                slot_updates = {}
                next_intent = self._determine_next_intent(current_intent, user_message, structured_data)
                
                return content, slot_updates, next_intent
                
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.logger.error(f"Error in guide conversation turn: {e}")
            # Fallback response
            if language == 'zh':
                return "我很想听你分享更多。请告诉我你今天的感受。", {}, current_intent
            else:
                return "I'd love to hear more from you. Tell me about how you're feeling today.", {}, current_intent
    
    def _clean_response(self, content: str) -> str:
        """Aggressively clean LLM response by removing ALL JSON artifacts and technical content"""
        import re
        
        # STEP 1: Remove all code blocks, backticks, and thinking blocks
        content = re.sub(r'```[^`]*```', '', content, flags=re.DOTALL)
        content = re.sub(r'`[^`]*`', '', content, flags=re.DOTALL)
        content = content.replace('```', '')
        content = content.replace('`', '')
        
        # Remove Qwen thinking blocks: <think>...</think> (complete and incomplete)
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove incomplete thinking blocks (where response was cut off)
        content = re.sub(r'<think>.*$', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<thinking>.*$', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove Chinese reasoning patterns - comprehensive
        content = re.sub(r'接下来，.*?。', '', content, flags=re.DOTALL)
        content = re.sub(r'用户.*?，所以我.*?。', '', content, flags=re.DOTALL)
        content = re.sub(r'我要.*?，.*?。', '', content, flags=re.DOTALL)
        content = re.sub(r'同时，要.*?。', '', content, flags=re.DOTALL)
        content = re.sub(r'另外，用户.*', '', content, flags=re.DOTALL)
        content = re.sub(r'这样.*?还能.*?。', '', content, flags=re.DOTALL)
        
        # STEP 2: Remove JSON objects - multiple approaches for maximum coverage
        # Remove any content between curly braces (including nested)
        while '{' in content and '}' in content:
            # Find the first { and matching }
            start = content.find('{')
            if start == -1:
                break
            brace_count = 0
            end = start
            for i in range(start, len(content)):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i
                        break
            if brace_count == 0:
                content = content[:start] + content[end+1:]
            else:
                break
        
        # STEP 3: Remove specific technical keywords and phrases
        technical_keywords = [
            'slot_updates', 'next_intent', 'json', 'JSON',
            '"mood":', '"activities":', '"challenges":', '"gratitude":', '"hope":', '"extra_notes":',
            'ASK_MOOD', 'ASK_ACTIVITIES', 'ASK_CHALLENGES_WINS', 'ASK_GRATITUDE', 'ASK_HOPE', 'ASK_EXTRA',
            '<think>', '</think>', '<thinking>', '</thinking>'
        ]
        
        for keyword in technical_keywords:
            content = content.replace(keyword, '')
        
        # STEP 4: Line-by-line filtering - remove any line containing technical content
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line_clean = line.strip()
            # Skip empty lines initially
            if not line_clean:
                continue
                
            # Skip lines that contain any technical indicators or Chinese reasoning patterns
            skip_line = False
            technical_indicators = ['{', '}', '":', 'slot_updates', 'next_intent', 'json', 'JSON', '<think>', '</think>', '<thinking>', '</thinking>']
            reasoning_patterns = ['用户可能', '我要', '所以我', '这样能', '另外，', '同时，', '接下来，', '因此我', '我应该', '这时候']
            
            for indicator in technical_indicators:
                if indicator in line_clean:
                    skip_line = True
                    break
            
            # Check for Chinese reasoning patterns
            if not skip_line:
                for pattern in reasoning_patterns:
                    if pattern in line_clean:
                        skip_line = True
                        break
            
            # Skip lines that are mostly punctuation or technical chars
            if len(line_clean) > 0:
                non_alpha_ratio = sum(1 for c in line_clean if not c.isalpha() and not c.isspace()) / len(line_clean)
                if non_alpha_ratio > 0.6:  # If more than 60% is non-alphabetic
                    skip_line = True
            
            if not skip_line and line_clean:
                cleaned_lines.append(line.rstrip())
        
        # STEP 5: Rejoin and final cleanup
        content = '\n'.join(cleaned_lines)
        
        # Remove extra whitespace
        content = re.sub(r'\n\s*\n+', '\n\n', content)
        content = re.sub(r'^\s+|\s+$', '', content)
        
        # STEP 6: Final validation - if result is too short or empty, provide fallback
        if len(content.strip()) < 10:
            content = "很想听你分享更多。你在斯里兰卡有什么特别的体验吗？"
        
        return content.strip()
    
    def _determine_next_intent(self, current_intent: str, user_message: str, structured_data: Dict) -> str:
        """Determine the next intent based on current state and user input"""
        
        # Define the conversation flow
        flow_map = {
            'ASK_MOOD': 'ASK_ACTIVITIES',
            'ASK_ACTIVITIES': 'ASK_CHALLENGES_WINS',
            'ASK_CHALLENGES_WINS': 'ASK_GRATITUDE',
            'ASK_GRATITUDE': 'ASK_HOPE',
            'ASK_HOPE': 'ASK_EXTRA',
            'ASK_EXTRA': 'COMPOSE'
        }
        
        # Check for crisis indicators
        crisis_keywords = [
            'hurt myself', 'kill myself', 'end my life', 'suicide', 'self-harm',
            '伤害自己', '自杀', '结束生命', '想死'
        ]
        
        if any(keyword.lower() in user_message.lower() for keyword in crisis_keywords):
            return 'CRISIS_FLOW'
        
        # Check for diary generation trigger in ASK_EXTRA phase
        if current_intent == 'ASK_EXTRA':
            # Check if user is asking to generate diary
            diary_triggers = [
                'generate', 'create', 'diary', 'ready', 'done', 'finished',
                '生成', '创建', '日记', '准备', '完成', '结束'
            ]
            if any(trigger in user_message.lower() for trigger in diary_triggers):
                return 'COMPOSE'
            else:
                # Stay in ASK_EXTRA to show the generate button
                return 'ASK_EXTRA'
        
        # Move to next step if user provided substantive response (more than a few words)
        if len(user_message.strip().split()) >= 2:  # Reduced from 3 to 2 words
            return flow_map.get(current_intent, 'COMPOSE')
        else:
            # Stay on current intent if response is too brief, but don't get stuck
            return current_intent
    
    def _extract_slot_data(self, intent: str, user_message: str, structured_data: Dict) -> Dict:
        """Extract relevant data from user message for the current intent"""
        
        slot_updates = {}
        
        # Simple keyword-based extraction (could be enhanced with NLP)
        if intent == 'ASK_MOOD' and not structured_data.get('mood'):
            slot_updates['mood'] = user_message
        elif intent == 'ASK_ACTIVITIES' and not structured_data.get('activities'):
            slot_updates['activities'] = user_message
        elif intent == 'ASK_CHALLENGES_WINS' and not structured_data.get('challenges'):
            slot_updates['challenges'] = user_message
        elif intent == 'ASK_GRATITUDE' and not structured_data.get('gratitude'):
            slot_updates['gratitude'] = user_message
        elif intent == 'ASK_HOPE' and not structured_data.get('hope'):
            slot_updates['hope'] = user_message
        elif intent == 'ASK_EXTRA' and not structured_data.get('extra_notes'):
            slot_updates['extra_notes'] = user_message
        
        return slot_updates
    
    def compose_diary_entry(self,
                           structured_data: Dict,
                           language: str = 'en',
                           model_name: Optional[str] = None) -> str:
        """
        Compose diary entry from structured data
        """
        
        if not model_name:
            model_name = self.default_models.get(language, 'gemma3:4b')
        
        # Ensure model is available
        if not self.check_model_availability(model_name):
            if not self.pull_model(model_name):
                raise Exception(f"Model {model_name} not available and couldn't be pulled")
        
        # Build prompt with structured data
        system_prompt = self.composer_prompts[language]
        
        # Create context from structured data
        today_date = datetime.now().strftime('%Y-%m-%d')
        
        if language == 'zh':
            context_prompt = f"""请基于以下结构化数据写一篇个人日记条目（{today_date}）：

{json.dumps(structured_data, ensure_ascii=False, indent=2)}

只使用提供的信息，不要添加任何虚构的细节。"""
        else:
            context_prompt = f"""Please write a personal diary entry based on the following structured data from {today_date}:

{json.dumps(structured_data, ensure_ascii=False, indent=2)}

Use only the information provided. Do not add any fictional details."""
        
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
                return content
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.logger.error(f"Error composing diary entry: {e}")
            # Fallback to template-based generation
            return self._fallback_diary_generation(structured_data, language)
    
    def _fallback_diary_generation(self, structured_data: Dict, language: str) -> str:
        """Fallback diary generation when LLM fails"""
        if language == 'zh':
            return "今天是新的一天。我正在学会记录和反思我的日常生活。这个过程帮助我更好地了解自己。"
        else:
            return "Today was a new day. I'm learning to document and reflect on my daily life. This process helps me understand myself better."