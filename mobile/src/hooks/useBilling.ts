import { useMemo } from "react";
import { canUse as engineCanUse, ENTITLEMENTS, isElite, isFree, isPro, BillingStatus } from "../lib/UserAccessEngine";
import { useUserContext } from "../context/UserContext";

type Feature = keyof typeof ENTITLEMENTS;

type BillingHelpers = {
  status: BillingStatus | null;
  loading: boolean;
  userId: string;
  refresh: () => Promise<BillingStatus | null>;
  isFree: boolean;
  isPro: boolean;
  isElite: boolean;
  canUse: (feature: Feature) => boolean;
};

export function useBilling(): BillingHelpers {
  const { status, loading, userId, refresh } = useUserContext();

  return useMemo(() => {
    const current = status ?? { userId, tier: "free" as const };
    return {
      status,
      loading,
      userId,
      refresh,
      isFree: isFree(current),
      isPro: isPro(current),
      isElite: isElite(current),
      canUse: (feature: Feature) => engineCanUse(feature, current)
    };
  }, [loading, refresh, status, userId]);
}
