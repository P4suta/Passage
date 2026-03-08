import type { CachePort } from "../port/cache-port.js";

export class KvCacheAdapter implements CachePort {
	constructor(private readonly kv: KVNamespace) {}

	async get<T>(key: string): Promise<T | null> {
		const value = await this.kv.get(key, "json");
		return value as T | null;
	}

	async set<T>(key: string, value: T, ttlSeconds: number): Promise<void> {
		await this.kv.put(key, JSON.stringify(value), {
			expirationTtl: ttlSeconds,
		});
	}

	async increment(key: string, ttlSeconds: number): Promise<number> {
		const current = (await this.kv.get(key, "json")) as number | null;
		const next = (current ?? 0) + 1;
		await this.kv.put(key, JSON.stringify(next), {
			expirationTtl: ttlSeconds,
		});
		return next;
	}
}
