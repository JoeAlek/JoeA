import aiohttp
import logging
import random
import json
import os
import asyncio
import time
import google.generativeai as genai
from functools import lru_cache
from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    MAX_TOKENS, 
    TEMPERATURE, 
    ENABLE_CACHING,
    RESPONSE_TIMEOUT,
    CONCURRENT_REQUESTS,
    BOT_NAME,
    BOT_OWNER
)

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.model = GEMINI_MODEL
        self.max_tokens = MAX_TOKENS
        self.temperature = TEMPERATURE
        self.enable_caching = ENABLE_CACHING
        self.response_timeout = RESPONSE_TIMEOUT
        
        # Semaphore to limit concurrent API requests
        self.request_semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
        
        # Initialize response cache
        self.response_cache = {}
        self.cache_ttl = 3600  # Cache TTL in seconds (1 hour)
        
        if not self.api_key:
            logger.warning("Gemini API key not set! AI chat functionality will not work.")
        else:
            # Configure Gemini API
            genai.configure(api_key=self.api_key)
        
        # Session for API requests (for availability checks)
        self.session = None
    
    async def _get_session(self):
        """Get or create an aiohttp ClientSession."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.response_timeout)
            )
        return self.session
    
    def _get_cache_key(self, prompt, user_id=None):
        """Generate a cache key for a given prompt and user."""
        cache_key = f"{prompt}:{user_id if user_id else 'anonymous'}"
        return cache_key
    
    def _check_cache(self, prompt, user_id=None):
        """Check if a response is in the cache and still valid."""
        if not self.enable_caching:
            return None
        
        cache_key = self._get_cache_key(prompt, user_id)
        cached_item = self.response_cache.get(cache_key)
        
        if cached_item:
            timestamp, response = cached_item
            if time.time() - timestamp < self.cache_ttl:
                logger.info(f"Cache hit for prompt: {prompt[:30]}...")
                return response
            else:
                # Remove expired cache entry
                del self.response_cache[cache_key]
        
        return None
    
    def _update_cache(self, prompt, response, user_id=None):
        """Update the cache with a new response."""
        if not self.enable_caching:
            return
        
        cache_key = self._get_cache_key(prompt, user_id)
        self.response_cache[cache_key] = (time.time(), response)
        
        # Clean up old cache entries if cache is getting too large
        if len(self.response_cache) > 100:  # Max 100 cached responses
            oldest_key = min(self.response_cache.keys(), key=lambda k: self.response_cache[k][0])
            del self.response_cache[oldest_key]
    
    async def generate_response(self, prompt, user_id=None):
        """Generate an AI response based on the given prompt."""
        if not self.api_key:
            return "Sorry, the AI service is not configured properly. Please contact the bot administrator."
        
        # Check cache first
        cached_response = self._check_cache(prompt, user_id)
        if cached_response:
            return cached_response
        
        try:
            # Acquire semaphore to limit concurrent requests
            async with self.request_semaphore:
                # Create system prompt
                system_prompt = f"You are {BOT_NAME}, a helpful Discord bot created by {BOT_OWNER}. Your responses should be concise, informative, and friendly."
                
                try:
                    # Configure the model
                    generation_config = {
                        "max_output_tokens": self.max_tokens,
                        "temperature": self.temperature,
                    }
                    
                    # Get Gemini model
                    model = genai.GenerativeModel(
                        model_name=self.model,
                        generation_config=generation_config
                    )
                    
                    # Create the prompt with system message and user query
                    chat = model.start_chat(history=[])
                    
                    # Execute in a separate thread to avoid blocking
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None, 
                        lambda: chat.send_message(
                            f"{system_prompt}\n\nUser question: {prompt}"
                        )
                    )
                    
                    # Extract the text response
                    ai_response = response.text.strip()
                    
                    # Update cache
                    self._update_cache(prompt, ai_response, user_id)
                    
                    return ai_response
                    
                except Exception as api_error:
                    logger.error(f"Gemini API error: {api_error}")
                    
                    # Fallback responses if the API is not available
                    fallback_responses = [
                        "I'm thinking about that...",
                        "That's an interesting question!",
                        "Let me consider that for a moment.",
                        "I'd love to chat about that topic.",
                        "I'm here to help with your questions.",
                        "Thanks for asking. I'm processing that."
                    ]
                    return random.choice(fallback_responses)
        
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "Sorry, I encountered an error while generating a response. Please try again later."
    
    async def is_available(self):
        """Check if the AI service is available."""
        if not self.api_key:
            logger.error("API key is not set, AI service is not available")
            return False
            
        try:
            # Use Gemini API directly to test availability
            logger.info(f"Testing Gemini API availability with model: {self.model}")
            
            # Create simple generation config with minimal tokens
            generation_config = {
                "max_output_tokens": 5,
                "temperature": 0.1,
            }
            
            try:
                # Get Gemini model and run a simple test
                model = genai.GenerativeModel(
                    model_name=self.model,
                    generation_config=generation_config
                )
                
                # Execute in a separate thread to avoid blocking
                loop = asyncio.get_event_loop()
                
                # Use a simple timeout for this test
                test_task = loop.run_in_executor(
                    None, 
                    lambda: model.generate_content("Hi")
                )
                
                # Wait for response with timeout
                await asyncio.wait_for(test_task, timeout=10)
                
                logger.info("Gemini API is available")
                return True
                
            except asyncio.TimeoutError:
                logger.error("Gemini API availability check timed out")
                return False
            
            except Exception as api_error:
                logger.error(f"Gemini API error during availability check: {api_error}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking Gemini API availability: {e}")
            return False
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
