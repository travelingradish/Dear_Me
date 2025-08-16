import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from prompt_manager import PromptManager

class GuidedLLMService:
    """Service for managing guided diary conversation flow with separate Guide and Composer phases"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ollama_url = "http://127.0.0.1:11434"
        self.prompt_manager = PromptManager()
        
        # Default model selections
        self.default_models = {
            'en': 'llama3.1:8b',  # High-quality model for English conversations
            'zh': 'qwen3:8b'      # Better for Chinese conversations
        }
        
        # Fallback models if preferred ones aren't available
        self.fallback_models = {
            'en': 'qwen3:8b',  # Use qwen3:8b as fallback for English too
            'zh': 'qwen3:8b'
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
                               model_name: Optional[str] = None,
                               user_memories: Optional[List] = None) -> Tuple[str, Dict, str]:
        """
        Process one turn of guided conversation
        Returns: (assistant_response, slot_updates, next_intent)
        """
        
        if not model_name:
            model_name = self.default_models.get(language, 'llama3.1:8b')
        
        # Ensure model is available, try fallback if needed
        if not self.check_model_availability(model_name):
            self.logger.info(f"Primary model {model_name} not available, trying fallback")
            fallback = self.fallback_models.get(language, 'gemma3:4b')
            if self.check_model_availability(fallback):
                model_name = fallback
                self.logger.info(f"Using fallback model: {model_name}")
            else:
                if not self.pull_model(model_name):
                    raise Exception(f"Model {model_name} not available and couldn't be pulled")
        
        # Build conversation context
        system_prompt = self.prompt_manager.get_prompt("guided", language, "guide")
        
        # Add memory context if available
        if user_memories:
            from memory_service import MemoryService
            memory_service = MemoryService()
            memory_context = memory_service.format_memories_for_prompt(user_memories, language)
            if memory_context:
                system_prompt += f"\n\n{memory_context}\nUse this information to personalize your guidance and questions, but keep the conversation natural."
        
        # Build more comprehensive conversation context
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history for better context
        for msg in conversation_history[-6:]:  # Last 6 messages for better context
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        # Add current user message with intent context
        context = f"""Previous conversation shows we're at intent: {current_intent}

{user_message}

CRITICAL: Respond with natural conversation only. No JSON, code blocks, or technical content."""
        
        messages.append({"role": "user", "content": context})
        
        try:
            payload = {
                'model': model_name,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': 0.8,      # Slightly higher for more natural conversation
                    'top_p': 0.9,
                    'num_predict': 300,      # Appropriate length for conversation turns
                    'num_ctx': 8192,         # Larger context window for better memory
                    'repeat_penalty': 1.1,   # Reduce repetitive phrases
                    'stop': ['<think>', '<thinking>', 'User:', 'Assistant:']  # Stop on thinking tags and roles
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
        
        # Extract and accumulate responses based on conversation intent
        # Allow appending to existing data to capture full conversations
        if intent == 'ASK_MOOD':
            existing = structured_data.get('mood', '')
            if existing:
                slot_updates['mood'] = f"{existing} {user_message}".strip()
            else:
                slot_updates['mood'] = user_message
        elif intent == 'ASK_ACTIVITIES':
            existing = structured_data.get('activities', '')
            if existing:
                slot_updates['activities'] = f"{existing} {user_message}".strip()
            else:
                slot_updates['activities'] = user_message
        elif intent == 'ASK_CHALLENGES_WINS':
            existing = structured_data.get('challenges', '')
            if existing:
                slot_updates['challenges'] = f"{existing} {user_message}".strip()
            else:
                slot_updates['challenges'] = user_message
        elif intent == 'ASK_GRATITUDE':
            existing = structured_data.get('gratitude', '')
            if existing:
                slot_updates['gratitude'] = f"{existing} {user_message}".strip()
            else:
                slot_updates['gratitude'] = user_message
        elif intent == 'ASK_HOPE':
            existing = structured_data.get('hope', '')
            if existing:
                slot_updates['hope'] = f"{existing} {user_message}".strip()
            else:
                slot_updates['hope'] = user_message
        elif intent == 'ASK_EXTRA':
            existing = structured_data.get('extra_notes', '')
            if existing:
                slot_updates['extra_notes'] = f"{existing} {user_message}".strip()
            else:
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
            model_name = self.default_models.get(language, 'llama3.1:8b')
        
        # Ensure model is available
        if not self.check_model_availability(model_name):
            if not self.pull_model(model_name):
                raise Exception(f"Model {model_name} not available and couldn't be pulled")
        
        # Build prompt with structured data
        system_prompt = self.prompt_manager.get_prompt("guided", language, "composer")
        
        # Create context from structured data
        today_date = datetime.now().strftime('%Y-%m-%d')
        
        if language == 'zh':
            context_prompt = f"""请基于以下结构化数据写一篇个人日记条目（数据收集日期：{today_date}）：

{json.dumps(structured_data, ensure_ascii=False, indent=2)}

严格要求：
- 只使用上述结构化数据中的信息
- 如果任何字段为空或包含空字符串，完全跳过该主题
- 绝不编造任何人物、事件、地点、活动或情感
- 绝不在日记中写任何日期或时间
- 每个细节必须直接来自提供的数据"""
        else:
            context_prompt = f"""Please write a personal diary entry based on the following structured data (collected on {today_date}):

{json.dumps(structured_data, ensure_ascii=False, indent=2)}

STRICT REQUIREMENTS:
- Use ONLY the information from the structured data above
- If any field is empty or contains empty strings, skip that topic completely
- Do NOT invent any people, events, locations, activities, or emotions
- Do NOT include any dates or times in the diary entry itself
- Every detail must come directly from the provided data"""
        
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