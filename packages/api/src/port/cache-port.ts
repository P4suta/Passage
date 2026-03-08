export interface CachePort {
	get<T>(key: string): Promise<T | null>;
	set<T>(key: string, value: T, ttlSeconds: number): Promise<void>;
	increment(key: string, ttlSeconds: number): Promise<number>;
}
