import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app.services.prompt_manager import PromptManager

class GuidedLLMService:
    """Service for managing guided diary conversation flow with separate Guide and Composer phases"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ollama_url = "http://127.0.0.1:11434"
        self.prompt_manager = PromptManager()
        
        # Use llama3.1:8b for all languages
        self.default_model = 'llama3.1:8b'
        
    
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
                               user_memories: Optional[List] = None,
                               character_name: str = "AI Assistant") -> Tuple[str, Dict, str]:
        """
        Process one turn of guided conversation
        Returns: (assistant_response, slot_updates, next_intent)
        """
        
        # Use our single model for all languages
        model_name = self.default_model
        
        # Ensure model is available
        if not self.check_model_availability(model_name):
            if not self.pull_model(model_name):
                raise Exception(f"Model {model_name} not available and couldn't be pulled")
        
        # Build conversation context
        system_prompt = self.prompt_manager.get_prompt("guided", language, "guide")
        
        # Inject character name into prompt
        if character_name != "AI Assistant":
            if language == 'zh':
                character_instruction = f"\n\n重要：你的名字是{character_name}。在对话中自然地使用这个名字来称呼自己，让对话更个性化。"
            else:
                character_instruction = f"\n\nIMPORTANT: Your name is {character_name}. Use this name naturally when referring to yourself in conversation to make it more personal."
            system_prompt += character_instruction
        
        # Add memory context if available
        if user_memories:
            from app.services.memory_service import MemoryService
            memory_service = MemoryService()
            # Pass user message as context for better memory filtering
            memory_context = memory_service.format_memories_for_prompt(user_memories, language, user_message)
            if memory_context:
                system_prompt += f"\n\n{memory_context}\nUse this information sparingly and only when directly relevant to personalize your guidance."
        
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
                content = self._clean_response(content, language, current_intent)
                
                # Extract structured data from user message
                slot_updates = self._extract_slot_updates(user_message, current_intent, language)
                next_intent = self._determine_next_intent(current_intent, user_message, structured_data, slot_updates)
                
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
    
    def _clean_response(self, content: str, language: str = 'en', current_intent: str = 'ASK_MOOD') -> str:
        """Aggressively clean LLM response by removing ALL JSON artifacts and technical content"""
        import re
        
        # STEP 1: Remove all code blocks, backticks, and thinking blocks
        content = re.sub(r'```[^`]*```', '', content, flags=re.DOTALL)
        content = re.sub(r'`[^`]*`', '', content, flags=re.DOTALL)
        content = content.replace('```', '')
        content = content.replace('`', '')
        
        # Remove ALL reasoning and thinking blocks from ANY reasoning model
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<thought>.*?</thought>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<reasoning>.*?</reasoning>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove incomplete thinking blocks (where response was cut off)
        content = re.sub(r'<think>.*$', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<thinking>.*$', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<thought>.*$', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<reasoning>.*$', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove reasoning patterns from the beginning of text
        content = re.sub(r'^.*?<think>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'^.*?<thinking>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
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
            # Context-aware fallback responses
            content = self._get_contextual_fallback(language, current_intent)
        
        return content.strip()
    
    def _get_contextual_fallback(self, language: str, current_intent: str) -> str:
        """Provide appropriate fallback responses based on language and conversation context"""
        
        # Chinese fallbacks based on conversation intent
        if language == 'zh':
            fallbacks = {
                'ASK_MOOD': '你今天感觉怎么样呢？',
                'ASK_ACTIVITIES': '你今天做了什么有趣的事情吗？',
                'ASK_CHALLENGES_WINS': '今天有没有遇到什么挑战或收获？',
                'ASK_GRATITUDE': '今天有什么让你感恩的事情吗？',
                'ASK_HOPE': '对于明天或未来，你有什么期待吗？',
                'ASK_EXTRA': '今天还有什么想记录下来的吗？',
                'COMPOSE': '让我为你写下今天的日记吧。',
                'CRISIS_FLOW': '我很关心你现在的状况。你现在安全吗？'
            }
            return fallbacks.get(current_intent, '我很想听你分享更多。能告诉我你今天的感受吗？')
        
        # English fallbacks based on conversation intent
        else:
            fallbacks = {
                'ASK_MOOD': 'How are you feeling today?',
                'ASK_ACTIVITIES': 'What did you do today that was interesting?',
                'ASK_CHALLENGES_WINS': 'Did you face any challenges or experience wins today?',
                'ASK_GRATITUDE': 'Is there anything you feel grateful for today?',
                'ASK_HOPE': 'What are you looking forward to or feeling hopeful about?',
                'ASK_EXTRA': 'Is there anything else you would like to record about today?',
                'COMPOSE': "Let me create your diary entry based on what you've shared.",
                'CRISIS_FLOW': "I'm concerned about you right now. Are you in a safe place?"
            }
            return fallbacks.get(current_intent, "I'd love to hear more from you. Tell me about how you're feeling today.")
    
    def _extract_slot_updates(self, user_message: str, current_intent: str, language: str) -> Dict:
        """Extract structured data from user message based on current intent"""
        
        # Initialize updates
        slot_updates = {}
        user_message_lower = user_message.lower()
        
        # Intent-specific extraction
        if current_intent == 'ASK_MOOD':
            slot_updates['mood'] = self._extract_mood(user_message, language)
        
        elif current_intent == 'ASK_ACTIVITIES':
            slot_updates['activities'] = self._extract_activities(user_message, language)
        
        elif current_intent == 'ASK_CHALLENGES_WINS':
            challenges, wins = self._extract_challenges_wins(user_message, language)
            if challenges:
                slot_updates['challenges'] = challenges
            if wins:
                slot_updates['wins'] = wins
        
        elif current_intent == 'ASK_GRATITUDE':
            slot_updates['gratitude'] = self._extract_gratitude(user_message, language)
        
        elif current_intent == 'ASK_HOPE':
            slot_updates['hope'] = self._extract_hope(user_message, language)
        
        elif current_intent == 'ASK_EXTRA':
            slot_updates['extra_notes'] = self._extract_extra_notes(user_message, language)
        
        # Remove empty updates
        return {k: v for k, v in slot_updates.items() if v and v.strip()}
    
    def _extract_mood(self, message: str, language: str) -> str:
        """Extract mood/emotional state from message"""
        if not message or len(message.strip()) < 3:
            return ""
        
        # Just return the relevant parts of the message that describe mood
        message = message.strip()
        if len(message) > 200:
            message = message[:200] + "..."
        return message
    
    def _extract_activities(self, message: str, language: str) -> str:
        """Extract activities/events from message"""
        if not message or len(message.strip()) < 3:
            return ""
        
        message = message.strip()
        if len(message) > 200:
            message = message[:200] + "..."
        return message
    
    def _extract_challenges_wins(self, message: str, language: str) -> tuple:
        """Extract challenges and wins from message"""
        if not message or len(message.strip()) < 3:
            return "", ""
        
        message = message.strip()
        if len(message) > 200:
            message = message[:200] + "..."
        
        # For now, treat the entire message as either challenges or wins
        # More sophisticated extraction could be added later
        return message, ""
    
    def _extract_gratitude(self, message: str, language: str) -> str:
        """Extract gratitude from message"""
        if not message or len(message.strip()) < 3:
            return ""
        
        message = message.strip()
        if len(message) > 200:
            message = message[:200] + "..."
        return message
    
    def _extract_hope(self, message: str, language: str) -> str:
        """Extract hopes/future outlook from message"""
        if not message or len(message.strip()) < 3:
            return ""
        
        message = message.strip()
        if len(message) > 200:
            message = message[:200] + "..."
        return message
    
    def _extract_extra_notes(self, message: str, language: str) -> str:
        """Extract additional notes from message"""
        if not message or len(message.strip()) < 3:
            return ""
        
        message = message.strip()
        if len(message) > 200:
            message = message[:200] + "..."
        return message
    
    def _determine_next_intent(self, current_intent: str, user_message: str, structured_data: Dict, slot_updates: Dict = None) -> str:
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
        
        # Smarter intent progression based on information completeness
        if self._has_sufficient_information(current_intent, user_message, slot_updates):
            return flow_map.get(current_intent, 'COMPOSE')
        else:
            # Stay on current intent if response is insufficient
            return current_intent
    
    def _has_sufficient_information(self, current_intent: str, user_message: str, slot_updates: Dict) -> bool:
        """Check if user provided sufficient information for current intent"""
        
        if not user_message or not user_message.strip():
            return False
        
        message = user_message.strip()
        
        # Use character count for Chinese, word count for English
        # Chinese text doesn't use spaces between words
        if any('\u4e00' <= char <= '\u9fff' for char in message):  # Chinese character range
            # For Chinese, use character count
            message_length = len([char for char in message if char.isalpha() or '\u4e00' <= char <= '\u9fff'])
            # Character thresholds for Chinese
            intent_thresholds = {
                'ASK_MOOD': 5,           # "我感觉很好" (5 chars)
                'ASK_ACTIVITIES': 6,     # "我去跑步了" (6 chars) 
                'ASK_CHALLENGES_WINS': 6, # "今天很顺利" (6 chars)
                'ASK_GRATITUDE': 4,      # "感谢朋友" (4 chars)
                'ASK_HOPE': 6,           # "希望明天更好" (6 chars)
                'ASK_EXTRA': 3           # "没有了" (3 chars)
            }
        else:
            # For English, use word count
            message_words = message.split()
            message_length = len(message_words)
            intent_thresholds = {
                'ASK_MOOD': 2,           # "feeling tired", "good today"
                'ASK_ACTIVITIES': 3,     # "went to work", "stayed home today"
                'ASK_CHALLENGES_WINS': 3, # "difficult meeting", "completed project"
                'ASK_GRATITUDE': 2,      # "my family", "sunny weather"
                'ASK_HOPE': 3,           # "tomorrow will be better"
                'ASK_EXTRA': 2           # "nothing else", "that's all"
            }
        
        threshold = intent_thresholds.get(current_intent, 2)
        
        # Check if message meets minimum length
        if message_length < threshold:
            return False
        
        # Check for dismissive/non-informative responses
        dismissive_patterns = [
            'nothing', 'no', 'nope', 'not really', 'don\'t know', 'maybe', 'okay', 'fine',
            '没有', '不', '不知道', '也许', '好吧', '还行', '一般'
        ]
        
        message_lower = message.lower().strip()
        if message_lower in dismissive_patterns or len(message_lower) <= 3:
            return False
        
        # Check if we actually extracted any meaningful slot updates
        if slot_updates and any(v.strip() for v in slot_updates.values()):
            return True
        
        # If no slot updates but message is substantial, accept it
        return message_length >= threshold
    
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
    
    def process_guided_message(self,
                             user_message: str,
                             current_intent: str,
                             structured_data: Dict,
                             conversation_history: List[Dict],
                             language: str = 'en',
                             model_name: Optional[str] = None,
                             user_memories: List = None,
                             character_name: str = "AI Assistant") -> Dict:
        """
        Process user message in guided mode and return structured response
        Expected by DiaryFlowController
        """
        try:
            # Extract slot updates from user message
            slot_updates = self._extract_slot_updates(user_message, current_intent, language)
            
            # Determine next intent based on current state and response quality
            next_intent = self._determine_next_intent(current_intent, user_message, structured_data, slot_updates)
            
            # Check for crisis indicators
            is_crisis = self._check_for_crisis(user_message)
            if is_crisis:
                next_intent = 'CRISIS_FLOW'
            
            # Generate appropriate response for the current intent
            response = self._generate_guided_response(
                user_message, current_intent, next_intent, 
                structured_data, language, character_name
            )
            
            return {
                'response': response,
                'slot_updates': slot_updates,
                'next_intent': next_intent,
                'is_crisis': is_crisis
            }
            
        except Exception as e:
            self.logger.error(f"Error processing guided message: {e}")
            # Return safe fallback
            return {
                'response': self._get_contextual_fallback(language, current_intent),
                'slot_updates': {},
                'next_intent': current_intent,  # Stay on current intent if error
                'is_crisis': False
            }
    
    def _check_for_crisis(self, user_message: str) -> bool:
        """Check if user message contains crisis indicators"""
        crisis_keywords = [
            'hurt myself', 'kill myself', 'end my life', 'suicide', 'self-harm',
            'want to die', 'better off dead', 'no point living',
            '伤害自己', '自杀', '结束生命', '想死', '不想活', '活着没意思'
        ]
        
        message_lower = user_message.lower()
        return any(keyword in message_lower for keyword in crisis_keywords)
    
    def _generate_guided_response(self,
                                user_message: str,
                                current_intent: str,
                                next_intent: str,
                                structured_data: Dict,
                                language: str,
                                character_name: str) -> str:
        """Generate appropriate response for guided conversation"""
        
        # If we're moving to next intent, provide transition response
        if next_intent != current_intent and next_intent != 'CRISIS_FLOW':
            return self._get_transition_response(next_intent, language, character_name)
        
        # If staying on current intent, encourage more information
        elif next_intent == current_intent:
            return self._get_encouragement_response(current_intent, language, character_name)
        
        # Crisis response handled separately
        elif next_intent == 'CRISIS_FLOW':
            if language == 'zh':
                return "听到这些我很难过。你值得被支持。如果你正处在紧急危险中，请立刻拨打当地的紧急电话。"
            else:
                return "I'm really sorry you're going through this. You deserve support. If you're in immediate danger, please call your local emergency number."
        
        # Default fallback
        return self._get_contextual_fallback(language, current_intent)
    
    def _get_transition_response(self, next_intent: str, language: str, character_name: str) -> str:
        """Get response when transitioning to next intent"""
        if language == 'zh':
            responses = {
                'ASK_ACTIVITIES': '谢谢你的分享。你今天做了什么有趣的事情吗？',
                'ASK_CHALLENGES_WINS': '听起来很不错。今天有没有遇到什么挑战或收获？',
                'ASK_GRATITUDE': '很好。今天有什么让你感恩的事情吗？',
                'ASK_HOPE': '很棒。对于明天或未来，你有什么期待吗？',
                'ASK_EXTRA': '太好了。今天还有什么想记录下来的吗？',
                'COMPOSE': '谢谢你分享这么多。让我为你写今天的日记吧。'
            }
        else:
            responses = {
                'ASK_ACTIVITIES': 'Thanks for sharing that. What did you do today that was interesting?',
                'ASK_CHALLENGES_WINS': 'That sounds good. Did you face any challenges or experience wins today?',
                'ASK_GRATITUDE': 'Great. Is there anything you feel grateful for today?',
                'ASK_HOPE': 'Wonderful. What are you looking forward to or feeling hopeful about?',
                'ASK_EXTRA': 'Perfect. Is there anything else you would like to record about today?',
                'COMPOSE': 'Thank you for sharing so much with me. Let me create your diary entry for today.'
            }
        
        return responses.get(next_intent, self._get_contextual_fallback(language, next_intent))
    
    def _get_encouragement_response(self, current_intent: str, language: str, character_name: str) -> str:
        """Get encouraging response to stay on current intent"""
        if language == 'zh':
            responses = {
                'ASK_MOOD': '我想了解更多。能详细说说你今天的感受吗？',
                'ASK_ACTIVITIES': '听起来很有意思。能告诉我更多关于你今天做了什么吗？',
                'ASK_CHALLENGES_WINS': '我想听更多。能分享更多关于今天的挑战或收获吗？',
                'ASK_GRATITUDE': '这很好。还有其他让你感恩的事情吗？',
                'ASK_HOPE': '这很积极。还有其他让你期待的事情吗？',
                'ASK_EXTRA': '好的。还有什么想补充的吗？'
            }
        else:
            responses = {
                'ASK_MOOD': 'I\'d love to understand more. Can you tell me more about how you\'re feeling today?',
                'ASK_ACTIVITIES': 'That sounds interesting. Can you share more about what you did today?',
                'ASK_CHALLENGES_WINS': 'I\'d like to hear more. Can you share more about any challenges or wins today?',
                'ASK_GRATITUDE': 'That\'s wonderful. Is there anything else you feel grateful for?',
                'ASK_HOPE': 'That\'s positive. Is there anything else you\'re looking forward to?',
                'ASK_EXTRA': 'Okay. Is there anything else you\'d like to add?'
            }
        
        return responses.get(current_intent, self._get_contextual_fallback(language, current_intent))
    
    def get_initial_greeting(self, language: str, character_name: str) -> str:
        """Get initial greeting for starting a guided session"""
        if language == 'zh':
            return f"你好！😊 我是{character_name}。我在这里帮你回顾今天。你现在想聊什么？"
        else:
            return f"Hi there! 😊 I'm {character_name}. I'm here to help you reflect on your day. What's on your mind today?"

    def compose_diary_entry(self,
                           structured_data: Dict,
                           language: str = 'en',
                           model_name: Optional[str] = None,
                           character_name: str = "AI Assistant") -> str:
        """
        Compose diary entry from structured data
        """
        
        # Force use of llama3.1:8b for all languages - never use reasoning models
        model_name = 'llama3.1:8b'
        self.logger.info(f"Composing diary with model: {model_name}")
        
        # Ensure model is available
        if not self.check_model_availability(model_name):
            if not self.pull_model(model_name):
                raise Exception(f"Model {model_name} not available and couldn't be pulled")
        
        # Build prompt with structured data - clear cache to ensure latest prompt is used
        self.prompt_manager.clear_cache()
        system_prompt = self.prompt_manager.get_prompt("guided", language, "composer")
        
        # Inject character name into prompt
        if character_name != "AI Assistant":
            if language == 'zh':
                character_instruction = f"\n\n重要：以{character_name}的身份写日记，体现出个人化的特点。"
            else:
                character_instruction = f"\n\nIMPORTANT: Write the diary as {character_name} to reflect a personalized perspective."
            system_prompt += character_instruction
        
        # Create context from structured data
        today_date = datetime.now().strftime('%Y-%m-%d')
        
        # Format structured data naturally without technical field names
        data_parts = []
        
        if language == 'zh':
            if structured_data.get('mood'):
                data_parts.append(f"心情感受：{structured_data['mood']}")
            if structured_data.get('activities'):
                data_parts.append(f"今天的活动：{structured_data['activities']}")
            if structured_data.get('challenges'):
                data_parts.append(f"挑战或成就：{structured_data['challenges']}")
            if structured_data.get('gratitude'):
                data_parts.append(f"感恩的事情：{structured_data['gratitude']}")
            if structured_data.get('hope'):
                data_parts.append(f"未来期待：{structured_data['hope']}")
            if structured_data.get('extra_notes'):
                data_parts.append(f"其他想法：{structured_data['extra_notes']}")
            
            formatted_data = '\n'.join(data_parts)
            context_prompt = f"""请基于以下信息写一篇个人日记条目：

{formatted_data}

严格要求：
- 只使用上述提供的信息
- 写成第一人称日记形式
- 如果某项信息为空，跳过该主题
- 绝不编造任何细节
- 绝不在日记中写日期或署名
- 语言自然流畅，体现个人感受"""
        else:
            if structured_data.get('mood'):
                data_parts.append(f"How I felt: {structured_data['mood']}")
            if structured_data.get('activities'):
                data_parts.append(f"What I did: {structured_data['activities']}")
            if structured_data.get('challenges'):
                data_parts.append(f"Challenges or wins: {structured_data['challenges']}")
            if structured_data.get('gratitude'):
                data_parts.append(f"What I'm grateful for: {structured_data['gratitude']}")
            if structured_data.get('hope'):
                data_parts.append(f"What I'm looking forward to: {structured_data['hope']}")
            if structured_data.get('extra_notes'):
                data_parts.append(f"Other thoughts: {structured_data['extra_notes']}")
                
            formatted_data = '\n'.join(data_parts)
            context_prompt = f"""Please write a personal diary entry based on this information:

{formatted_data}

STRICT REQUIREMENTS:
- Use ONLY the information provided above
- Write in first person as a diary entry
- If any information is missing, skip that topic
- Do NOT invent any details
- Do NOT include dates or signatures in the diary
- Keep the language natural and personal"""
        
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
                
                # Clean any reasoning artifacts from diary content
                cleaned_content = self._clean_response(content, language)
                return cleaned_content
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
    
    def get_initial_greeting(self, language: str = 'en', character_name: str = "AI Assistant") -> str:
        """Generate an initial greeting for starting a guided diary session"""
        if language == 'zh':
            return f"你好！我是{character_name}。我来陪你一起回顾今天的经历，帮助你记录和反思。你今天过得怎么样？"
        else:
            return f"Hi there! 😊 I'm {character_name}. I'm here to help you reflect on your day and create a meaningful diary entry. What's on your mind today?"
    
    def process_guided_message(self, 
                              user_message: str,
                              current_intent: str,
                              structured_data: Dict,
                              conversation_history: List[Dict],
                              language: str = 'en',
                              model_name: Optional[str] = None,
                              user_memories: Optional[List] = None,
                              character_name: str = "AI Assistant") -> Dict:
        """
        Process guided message and return response in test-compatible format
        This method provides the interface expected by tests
        """
        # Use the existing guide_conversation_turn method
        assistant_response, slot_updates, next_intent = self.guide_conversation_turn(
            user_message=user_message,
            current_intent=current_intent,
            structured_data=structured_data,
            conversation_history=conversation_history,
            language=language,
            model_name=model_name,
            user_memories=user_memories,
            character_name=character_name
        )
        
        # Check for crisis
        is_crisis = next_intent == 'CRISIS_FLOW'
        
        # Return in test-expected format
        return {
            "response": assistant_response,
            "next_intent": next_intent,
            "slot_updates": slot_updates,
            "is_crisis": is_crisis
        }
    
    def compose_diary_entry_test_format(self,
                                        structured_data: Dict,
                                        language: str = 'en',
                                        model_name: Optional[str] = None,
                                        character_name: str = "AI Assistant") -> Dict:
        """
        Compose diary entry and return response in test-expected format
        This method provides the interface expected by tests for compose phase
        """
        # Use the existing compose_diary_entry method
        diary_content = self.compose_diary_entry(
            structured_data=structured_data,
            language=language,
            model_name=model_name,
            character_name=character_name
        )
        
        # Return in test-expected format for compose phase
        return {
            "response": f"Based on our conversation, here's your diary entry:\n\n{diary_content}",
            "next_intent": "COMPLETE",
            "slot_updates": {},
            "is_crisis": False,
            "phase_complete": True,
            "composed_diary": diary_content
        }