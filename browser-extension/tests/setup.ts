/**
 * Vitest Global Setup & Chrome API Mock
 */

const storageMock: Record<string, any> = {};

(global as any).chrome = {
  runtime: {
    id: 'test-clyde-extension-id',
    getURL: (path: string) => `chrome-extension://test-clyde-extension-id/${path}`,
    sendMessage: (_msg: any, callback?: (response: any) => void) => {
      if (callback) callback({ success: true });
      return Promise.resolve({ success: true });
    },
    onMessage: {
      addListener: () => {},
      removeListener: () => {}
    }
  },
  storage: {
    local: {
      get: (keys: string | string[] | Record<string, any>, callback?: (result: any) => void) => {
        const result: Record<string, any> = {};
        if (typeof keys === 'string') {
          result[keys] = storageMock[keys];
        } else if (Array.isArray(keys)) {
          keys.forEach(k => { result[k] = storageMock[k]; });
        }
        if (callback) callback(result);
        return Promise.resolve(result);
      },
      set: (items: Record<string, any>, callback?: () => void) => {
        Object.assign(storageMock, items);
        if (callback) callback();
        return Promise.resolve();
      },
      remove: (keys: string | string[], callback?: () => void) => {
        if (typeof keys === 'string') {
          delete storageMock[keys];
        } else if (Array.isArray(keys)) {
          keys.forEach(k => delete storageMock[k]);
        }
        if (callback) callback();
        return Promise.resolve();
      },
      clear: (callback?: () => void) => {
        for (const k in storageMock) delete storageMock[k];
        if (callback) callback();
        return Promise.resolve();
      }
    }
  },
  tabs: {
    query: (_queryInfo: any, callback?: (tabs: any[]) => void) => {
      const tabs = [{ id: 101, url: 'https://boards.greenhouse.io/demo/jobs/1', active: true }];
      if (callback) callback(tabs);
      return Promise.resolve(tabs);
    },
    sendMessage: (_tabId: number, _message: any, callback?: (response: any) => void) => {
      if (callback) callback({ success: true });
      return Promise.resolve({ success: true });
    }
  }
};
