import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useMemo,
  useState
} from 'react';

export type LanguageFilter = 'all' | 'fr' | 'moore' | 'dioula' | 'fulfulde';

interface FilterState {
  category: string;
  language: LanguageFilter;
  user: string;
}

interface FilterContextValue extends FilterState {
  setCategory: (value: string) => void;
  setLanguage: (value: LanguageFilter) => void;
  setUser: (value: string) => void;
}

const FilterContext = createContext<FilterContextValue | undefined>(undefined);

export const FilterProvider = ({ children }: { children: ReactNode }) => {
  const [category, setCategory] = useState<string>('all');
  const [language, setLanguage] = useState<LanguageFilter>('all');
  const [user, setUser] = useState<string>('all');

  const value = useMemo(
    () => ({ category, language, user, setCategory, setLanguage, setUser }),
    [category, language, user]
  );

  return <FilterContext.Provider value={value}>{children}</FilterContext.Provider>;
};

export const useFilters = () => {
  const context = useContext(FilterContext);
  if (!context) {
    throw new Error('useFilters must be used within FilterProvider');
  }
  return context;
};
