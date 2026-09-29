import React, { createContext, useContext, useState, useEffect } from 'react';
import { en } from './locales/en';
import { hi } from './locales/hi';
import { mr } from './locales/mr';

export type SupportedLanguage = 'en' | 'hi' | 'mr';

export interface LanguageContextType {
  lang: SupportedLanguage;
  setLanguage: (lang: SupportedLanguage) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
  languages: { code: SupportedLanguage; label: string; nativeName: string }[];
}

const dictionaries: Record<SupportedLanguage, any> = {
  en,
  hi,
  mr,
};

const languagesList: { code: SupportedLanguage; label: string; nativeName: string }[] = [
  { code: 'en', label: 'English', nativeName: 'English' },
  { code: 'hi', label: 'Hindi', nativeName: 'हिन्दी' },
  { code: 'mr', label: 'Marathi', nativeName: 'मराठी' },
];

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLangState] = useState<SupportedLanguage>(() => {
    const saved = localStorage.getItem('bhusetu_lang');
    if (saved === 'hi' || saved === 'HI') return 'hi';
    if (saved === 'mr' || saved === 'MR') return 'mr';
    return 'en';
  });

  const setLanguage = (newLang: SupportedLanguage) => {
    setLangState(newLang);
    localStorage.setItem('bhusetu_lang', newLang);
    document.documentElement.lang = newLang;
    window.dispatchEvent(new Event('bhusetu_lang_changed'));
  };

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  // Nested translation retriever with graceful English fallback
  const t = (key: string, params?: Record<string, string | number>): string => {
    const keys = key.split('.');

    const lookup = (dict: any): any => {
      let current = dict;
      for (const k of keys) {
        if (!current || typeof current !== 'object') return undefined;
        current = current[k];
      }
      return current;
    };

    let result = lookup(dictionaries[lang]);
    if (result === undefined) {
      result = lookup(dictionaries.en);
    }

    if (result === undefined || typeof result !== 'string') {
      // Graceful fallback to leaf key formatted cleanly, NEVER raw dot notation
      const leaf = keys[keys.length - 1];
      return leaf.replace(/([A-Z])/g, ' $1').replace(/^./, (str) => str.toUpperCase());
    }

    if (params) {
      let templated = result;
      for (const [pKey, pVal] of Object.entries(params)) {
        templated = templated.replace(new RegExp(`{${pKey}}`, 'g'), String(pVal));
      }
      return templated;
    }

    return result;
  };

  return (
    <LanguageContext.Provider value={{ lang, setLanguage, t, languages: languagesList }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useTranslation = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useTranslation must be used within a LanguageProvider');
  }
  return context;
};
