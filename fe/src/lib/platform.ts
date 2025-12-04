
export type UserOS = 'ios' | 'android' | 'macos' | 'windows' | 'linux' | 'chromebook' | 'unknown';


export interface PlatformOptions {
    ua?: string; 
    platform?: string; 
    maxTouchPoints?: number; 
}


function safeUA(ua?: string) {
    if (ua) return ua;
    if (typeof navigator !== 'undefined') return navigator.userAgent || '';
    return '';
}


export function getOS(options: PlatformOptions = {}): UserOS {
    const ua = (options.ua || safeUA(options.ua)).toLowerCase();
    const platform = (options.platform || (typeof navigator !== 'undefined' ? (navigator.platform || '') : '')).toLowerCase();
    const maxTouch = options.maxTouchPoints ?? (typeof navigator !== 'undefined' ? (navigator.maxTouchPoints || 0) : 0);

    if (platform === 'macintel' && maxTouch > 1) {
        return 'ios';
    }

    if (/iphone|ipad|ipod/.test(ua)) return 'ios';
    if (/android/.test(ua)) return 'android';
    if (/windows nt/.test(ua)) return 'windows';
    if (/mac os x|macintosh/.test(ua)) return 'macos';
    if (/cros/.test(ua)) return 'chromebook';
    if (/linux/.test(ua)) return 'linux';

    return 'unknown';
}

export function getMajorVersion(options: PlatformOptions = {}, os?: UserOS): number | null {
    const ua = (options.ua || safeUA(options.ua)).toLowerCase();
    const detected = os ?? getOS(options);

    if (detected === 'ios') {
        const browserVersion = ua.match(/version\/(\d+)(?:[._]\d+)?/i);
        if (browserVersion && browserVersion[1]) return parseInt(browserVersion[1], 10);

        const m = ua.match(/(?:cpu (?:iphone )?os|\bos)\s*(\d+)(?:[._](\d+))?/i);
        if (m && m[1]) return parseInt(m[1], 10);

        return null;
    }

    if (detected === 'android') {
        const m = ua.match(/android\s*(\d+)(?:[._]\d+)?/i);
        if (m && m[1]) return parseInt(m[1], 10);
        return null;
    }

    if (detected === 'windows') {
        const m = ua.match(/windows nt\s*(\d+)(?:\.(\d+))?/i);
        if (m && m[1]) return parseInt(m[1], 10);
        return null;
    }

    if (detected === 'macos') {
        const m = ua.match(/mac os x\s*(\d+)[._](\d+)?/i);
        if (m && m[1]) return parseInt(m[1], 10);
        return null;
    }

    if (detected === 'chromebook') {

        const m = ua.match(/cros\s*[a-z0-9_]*\s*(\d+)/i);
        if (m && m[1]) return parseInt(m[1], 10);
        return null;
    }

    return null;
}
export function getPlatformInfo(options: PlatformOptions = {}) {
    const os = getOS(options);
    const major = getMajorVersion(options, os);
    return { os, major } as { os: UserOS; major: number | null;};
}

export function isMobile(options: PlatformOptions = {}): boolean {
    const os = getOS(options);
    return os === 'ios' || os === 'android';
}