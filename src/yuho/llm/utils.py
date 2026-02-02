"""
LLM response caching and rate limiting utilities.
"""

from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json
import time
import threading
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cached LLM response."""
    response: str
    prompt_hash: str
    timestamp: datetime
    hit_count: int = 0


class ResponseCache:
    """
    LRU cache for LLM responses using content-hash keys.
    
    Caches responses based on a hash of the prompt, allowing
    repeated queries to avoid redundant LLM calls.
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        Initialize the response cache.
        
        Args:
            max_size: Maximum number of entries to cache
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._ttl = timedelta(seconds=ttl_seconds)
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
    
    def _hash_prompt(self, prompt: str, **kwargs) -> str:
        """Generate a content hash for a prompt and parameters."""
        # Include relevant kwargs in hash
        hash_content = json.dumps({
            "prompt": prompt,
            **{k: v for k, v in sorted(kwargs.items())},
        }, sort_keys=True)
        return hashlib.sha256(hash_content.encode()).hexdigest()[:16]
    
    def get(self, prompt: str, **kwargs) -> Optional[str]:
        """
        Get a cached response for a prompt.
        
        Args:
            prompt: The prompt to look up
            **kwargs: Additional parameters that affect the response
            
        Returns:
            Cached response or None if not found/expired
        """
        key = self._hash_prompt(prompt, **kwargs)
        
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if datetime.now() - entry.timestamp > self._ttl:
                del self._cache[key]
                self._misses += 1
                return None
            
            # Update hit count and move to end (LRU)
            entry.hit_count += 1
            self._cache[key] = entry  # Move to end
            self._hits += 1
            
            logger.debug(f"Cache hit for prompt hash {key}")
            return entry.response
    
    def put(self, prompt: str, response: str, **kwargs) -> None:
        """
        Store a response in the cache.
        
        Args:
            prompt: The prompt that produced the response
            response: The LLM response to cache
            **kwargs: Additional parameters that affect the response
        """
        key = self._hash_prompt(prompt, **kwargs)
        
        with self._lock:
            # Evict oldest entries if at capacity
            while len(self._cache) >= self._max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                logger.debug(f"Evicted cache entry {oldest_key}")
            
            self._cache[key] = CacheEntry(
                response=response,
                prompt_hash=key,
                timestamp=datetime.now(),
            )
            logger.debug(f"Cached response for prompt hash {key}")
    
    def invalidate(self, prompt: str, **kwargs) -> bool:
        """
        Remove a specific entry from the cache.
        
        Returns:
            True if an entry was removed, False otherwise
        """
        key = self._hash_prompt(prompt, **kwargs)
        
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
            }


@dataclass
class RateLimitState:
    """State for tracking rate limit window."""
    requests: int = 0
    window_start: float = field(default_factory=time.time)
    backoff_until: float = 0.0


class RateLimiter:
    """
    Rate limiter with exponential backoff for cloud API providers.
    
    Tracks request counts within time windows and enforces
    limits with configurable backoff on 429 responses.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_day: int = 10000,
        base_backoff_seconds: float = 1.0,
        max_backoff_seconds: float = 60.0,
        backoff_multiplier: float = 2.0,
    ):
        """
        Initialize the rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute
            requests_per_day: Maximum requests per day
            base_backoff_seconds: Initial backoff duration
            max_backoff_seconds: Maximum backoff duration
            backoff_multiplier: Multiplier for exponential backoff
        """
        self.rpm_limit = requests_per_minute
        self.rpd_limit = requests_per_day
        self.base_backoff = base_backoff_seconds
        self.max_backoff = max_backoff_seconds
        self.backoff_multiplier = backoff_multiplier
        
        self._minute_state = RateLimitState()
        self._day_state = RateLimitState()
        self._current_backoff = base_backoff_seconds
        self._consecutive_failures = 0
        self._lock = threading.Lock()
    
    def _reset_window_if_needed(self, state: RateLimitState, window_seconds: float) -> None:
        """Reset request count if window has elapsed."""
        now = time.time()
        if now - state.window_start >= window_seconds:
            state.requests = 0
            state.window_start = now
    
    def acquire(self) -> float:
        """
        Acquire permission to make a request.
        
        Returns:
            Number of seconds to wait before making the request.
            Returns 0.0 if request can proceed immediately.
        """
        with self._lock:
            now = time.time()
            
            # Check if in backoff period
            if now < self._minute_state.backoff_until:
                wait_time = self._minute_state.backoff_until - now
                logger.warning(f"Rate limiter: backoff active, wait {wait_time:.2f}s")
                return wait_time
            
            # Reset windows if needed
            self._reset_window_if_needed(self._minute_state, 60.0)
            self._reset_window_if_needed(self._day_state, 86400.0)
            
            # Check minute limit
            if self._minute_state.requests >= self.rpm_limit:
                wait_time = 60.0 - (now - self._minute_state.window_start)
                logger.warning(f"Rate limit reached (RPM), wait {wait_time:.2f}s")
                return max(0.0, wait_time)
            
            # Check day limit
            if self._day_state.requests >= self.rpd_limit:
                wait_time = 86400.0 - (now - self._day_state.window_start)
                logger.warning(f"Rate limit reached (RPD), wait {wait_time:.2f}s")
                return max(0.0, wait_time)
            
            # Increment counters
            self._minute_state.requests += 1
            self._day_state.requests += 1
            
            return 0.0
    
    def report_success(self) -> None:
        """Report a successful request, resetting backoff."""
        with self._lock:
            self._consecutive_failures = 0
            self._current_backoff = self.base_backoff
    
    def report_rate_limited(self) -> float:
        """
        Report a rate limit response (429), triggering backoff.
        
        Returns:
            Recommended wait time before retry
        """
        with self._lock:
            self._consecutive_failures += 1
            
            # Calculate exponential backoff
            backoff = min(
                self.base_backoff * (self.backoff_multiplier ** self._consecutive_failures),
                self.max_backoff,
            )
            self._current_backoff = backoff
            
            # Set backoff period
            now = time.time()
            self._minute_state.backoff_until = now + backoff
            
            logger.warning(
                f"Rate limited: backoff {backoff:.2f}s "
                f"(failure #{self._consecutive_failures})"
            )
            return backoff
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        with self._lock:
            now = time.time()
            return {
                "requests_this_minute": self._minute_state.requests,
                "requests_this_day": self._day_state.requests,
                "rpm_limit": self.rpm_limit,
                "rpd_limit": self.rpd_limit,
                "current_backoff": self._current_backoff,
                "consecutive_failures": self._consecutive_failures,
                "in_backoff": now < self._minute_state.backoff_until,
            }


class TokenCounter:
    """
    Token counting for context window management.
    
    Provides approximate token counts using simple heuristics
    or exact counts via tiktoken if available.
    """
    
    def __init__(self, model: str = "gpt-4"):
        """
        Initialize the token counter.
        
        Args:
            model: Model name for accurate tokenization (if tiktoken available)
        """
        self.model = model
        self._encoding = None
        self._use_tiktoken = False
        
        # Try to load tiktoken for accurate counting
        try:
            import tiktoken
            try:
                self._encoding = tiktoken.encoding_for_model(model)
                self._use_tiktoken = True
                logger.debug(f"Using tiktoken for {model}")
            except KeyError:
                self._encoding = tiktoken.get_encoding("cl100k_base")
                self._use_tiktoken = True
                logger.debug("Using tiktoken with cl100k_base encoding")
        except ImportError:
            logger.debug("tiktoken not available, using approximate counting")
    
    def count(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens in
            
        Returns:
            Token count (exact with tiktoken, approximate otherwise)
        """
        if self._use_tiktoken and self._encoding:
            return len(self._encoding.encode(text))
        
        # Approximate: ~4 chars per token (conservative estimate)
        return max(1, len(text) // 4)
    
    def fits_context(self, text: str, context_window: int, reserved: int = 1000) -> bool:
        """
        Check if text fits within context window.
        
        Args:
            text: Text to check
            context_window: Maximum context window size
            reserved: Tokens reserved for response
            
        Returns:
            True if text fits, False otherwise
        """
        token_count = self.count(text)
        available = context_window - reserved
        return token_count <= available
    
    def truncate_to_fit(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit.
        
        Args:
            text: Text to truncate
            max_tokens: Maximum allowed tokens
            
        Returns:
            Truncated text
        """
        if self._use_tiktoken and self._encoding:
            tokens = self._encoding.encode(text)
            if len(tokens) <= max_tokens:
                return text
            return self._encoding.decode(tokens[:max_tokens])
        
        # Approximate: ~4 chars per token
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."


class PromptCompressor:
    """
    Compress prompts for long statutes exceeding context window.
    
    Strategies:
    - Remove comments and whitespace
    - Summarize sections
    - Split into chunks
    """
    
    def __init__(self, token_counter: Optional[TokenCounter] = None):
        """Initialize the prompt compressor."""
        self.token_counter = token_counter or TokenCounter()
    
    def compress(
        self,
        text: str,
        max_tokens: int,
        preserve_structure: bool = True,
    ) -> str:
        """
        Compress text to fit within token limit.
        
        Args:
            text: Text to compress
            max_tokens: Maximum allowed tokens
            preserve_structure: Keep structural elements (headers, etc.)
            
        Returns:
            Compressed text
        """
        current_count = self.token_counter.count(text)
        if current_count <= max_tokens:
            return text
        
        # Strategy 1: Remove excessive whitespace
        compressed = self._remove_excessive_whitespace(text)
        if self.token_counter.count(compressed) <= max_tokens:
            return compressed
        
        # Strategy 2: Remove comments
        compressed = self._remove_comments(compressed)
        if self.token_counter.count(compressed) <= max_tokens:
            return compressed
        
        # Strategy 3: Truncate with summary
        if preserve_structure:
            return self._truncate_with_summary(compressed, max_tokens)
        
        # Final fallback: direct truncation
        return self.token_counter.truncate_to_fit(compressed, max_tokens)
    
    def _remove_excessive_whitespace(self, text: str) -> str:
        """Remove excessive whitespace while preserving structure."""
        import re
        # Replace multiple blank lines with single
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        # Remove trailing whitespace
        text = '\n'.join(line.rstrip() for line in text.splitlines())
        return text
    
    def _remove_comments(self, text: str) -> str:
        """Remove comment lines from Yuho code."""
        lines = text.splitlines()
        non_comment_lines = [
            line for line in lines
            if not line.strip().startswith('#') and not line.strip().startswith('//')
        ]
        return '\n'.join(non_comment_lines)
    
    def _truncate_with_summary(self, text: str, max_tokens: int) -> str:
        """Truncate text but include a summary notice."""
        # Reserve some tokens for summary notice
        summary_notice = "\n\n[... content truncated for context window ...]\n"
        summary_tokens = self.token_counter.count(summary_notice)
        
        available = max_tokens - summary_tokens
        if available <= 0:
            return summary_notice
        
        truncated = self.token_counter.truncate_to_fit(text, available)
        return truncated + summary_notice
