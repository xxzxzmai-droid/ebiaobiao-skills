import { useState, useCallback } from 'react';

export interface DistrictFilter {
  district: string | null;
  industry: string | null;
  setDistrict: (d: string | null) => void;
  setIndustry: (i: string | null) => void;
  reset: () => void;
  hasFilter: boolean;
}

/** 全局过滤状态：选中的区/行业，让所有面板联动。 */
export function useDistrictFilter(): DistrictFilter {
  const [district, setDistrict] = useState<string | null>(null);
  const [industry, setIndustry] = useState<string | null>(null);
  const reset = useCallback(() => {
    setDistrict(null);
    setIndustry(null);
  }, []);
  return {
    district,
    industry,
    setDistrict,
    setIndustry,
    reset,
    hasFilter: !!(district || industry),
  };
}
