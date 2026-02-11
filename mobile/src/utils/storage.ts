import EncryptedStorage from 'react-native-encrypted-storage';

export const secureStorage = {
  async set(key: string, value: string): Promise<void> {
    await EncryptedStorage.setItem(key, value);
  },

  async get(key: string): Promise<string | null> {
    return EncryptedStorage.getItem(key);
  },

  async remove(key: string): Promise<void> {
    await EncryptedStorage.removeItem(key);
  },

  async setObject<T>(key: string, value: T): Promise<void> {
    await EncryptedStorage.setItem(key, JSON.stringify(value));
  },

  async getObject<T>(key: string): Promise<T | null> {
    const raw = await EncryptedStorage.getItem(key);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as T;
    } catch {
      return null;
    }
  },

  async clear(): Promise<void> {
    await EncryptedStorage.clear();
  },
};
