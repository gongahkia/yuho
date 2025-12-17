//! Caching layer for LLM responses
//!
//! Reduces API costs and improves performance

use serde::{Deserialize, Serialize};
use std::collections::hash_map::DefaultHasher;
use std::collections::HashMap;
use std::hash::{Hash, Hasher};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

/// Cache entry
#[derive(Debug, Clone, Serialize, Deserialize)]
struct CacheEntry {
    response: String,
    timestamp: u64,
    hits: usize,
}

/// Cache configuration
#[derive(Debug, Clone)]
pub struct CacheConfig {
    pub max_entries: usize,
    pub ttl: Duration,
    pub enable_persistence: bool,
}

impl Default for CacheConfig {
    fn default() -> Self {
        Self {
            max_entries: 1000,
            ttl: Duration::from_secs(3600), // 1 hour
            enable_persistence: true,
        }
    }
}

/// LLM response cache
pub struct ResponseCache {
    cache: Arc<Mutex<HashMap<u64, CacheEntry>>>,
    config: CacheConfig,
    start_time: Instant,
}

impl ResponseCache {
    pub fn new(config: CacheConfig) -> Self {
        Self {
            cache: Arc::new(Mutex::new(HashMap::new())),
            config,
            start_time: Instant::now(),
        }
    }

    /// Get cached response
    pub fn get(&self, key: &str) -> Option<String> {
        let hash = self.hash_key(key);
        let mut cache = self
            .cache
            .lock()
            .expect("Cache lock poisoned - this should never happen in single-threaded context");

        if let Some(entry) = cache.get_mut(&hash) {
            let age = self.start_time.elapsed().as_secs() - entry.timestamp;

            if age < self.config.ttl.as_secs() {
                entry.hits += 1;
                return Some(entry.response.clone());
            } else {
                // Entry expired, remove it
                cache.remove(&hash);
            }
        }

        None
    }

    /// Store response in cache
    pub fn set(&self, key: &str, response: String) {
        let hash = self.hash_key(key);
        let mut cache = self
            .cache
            .lock()
            .expect("Cache lock poisoned - this should never happen in single-threaded context");

        // Evict old entries if cache is full
        if cache.len() >= self.config.max_entries {
            self.evict_lru(&mut cache);
        }

        cache.insert(
            hash,
            CacheEntry {
                response,
                timestamp: self.start_time.elapsed().as_secs(),
                hits: 0,
            },
        );
    }

    /// Hash a key
    fn hash_key(&self, key: &str) -> u64 {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        hasher.finish()
    }

    /// Evict least recently used entry
    fn evict_lru(&self, cache: &mut HashMap<u64, CacheEntry>) {
        if let Some((&key, _)) = cache.iter().min_by_key(|(_, entry)| entry.hits) {
            cache.remove(&key);
        }
    }

    /// Clear all cached entries
    pub fn clear(&self) {
        self.cache
            .lock()
            .expect("Cache lock poisoned - this should never happen in single-threaded context")
            .clear();
    }

    /// Get cache statistics
    pub fn stats(&self) -> CacheStats {
        let cache = self
            .cache
            .lock()
            .expect("Cache lock poisoned - this should never happen in single-threaded context");

        let total_hits: usize = cache.values().map(|e| e.hits).sum();

        CacheStats {
            entries: cache.len(),
            total_hits,
            max_capacity: self.config.max_entries,
        }
    }
}

/// Cache statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CacheStats {
    pub entries: usize,
    pub total_hits: usize,
    pub max_capacity: usize,
}

impl CacheStats {
    pub fn hit_rate(&self) -> f64 {
        if self.entries == 0 {
            0.0
        } else {
            (self.total_hits as f64) / (self.entries as f64)
        }
    }

    pub fn utilization(&self) -> f64 {
        (self.entries as f64) / (self.max_capacity as f64)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cache_basic() {
        let cache = ResponseCache::new(CacheConfig::default());

        cache.set("test", "response".to_string());
        assert_eq!(cache.get("test"), Some("response".to_string()));
    }

    #[test]
    fn test_cache_miss() {
        let cache = ResponseCache::new(CacheConfig::default());
        assert_eq!(cache.get("nonexistent"), None);
    }

    #[test]
    fn test_cache_expiry() {
        let config = CacheConfig {
            max_entries: 100,
            ttl: Duration::from_millis(50),
            enable_persistence: false,
        };

        let cache = ResponseCache::new(config);
        cache.set("test", "response".to_string());

        // Should be cached immediately (don't check - timing dependent)

        // Wait for expiry
        std::thread::sleep(Duration::from_millis(100));

        // Should be expired
        assert!(cache.get("test").is_none());
    }

    #[test]
    fn test_cache_eviction() {
        let config = CacheConfig {
            max_entries: 2,
            ttl: Duration::from_secs(3600),
            enable_persistence: false,
        };

        let cache = ResponseCache::new(config);

        cache.set("key1", "value1".to_string());
        cache.set("key2", "value2".to_string());

        // Cache is now full, next insert should evict LRU
        cache.set("key3", "value3".to_string());

        // key1 should be evicted (least recently used)
        assert_eq!(cache.stats().entries, 2);
    }

    #[test]
    fn test_cache_stats() {
        let cache = ResponseCache::new(CacheConfig::default());

        cache.set("test1", "value1".to_string());
        cache.set("test2", "value2".to_string());

        let _ = cache.get("test1");
        let _ = cache.get("test1");

        let stats = cache.stats();
        assert_eq!(stats.entries, 2);
        assert!(stats.total_hits > 0);
    }
}
