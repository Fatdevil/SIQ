import { useMemo } from 'react';
import { BillingStatus, canUse as engineCanUse, ENTITLEMENTS, isElite, isFree, isPro } from '@/lib/UserAccessEngine';
import { useUserContext } from '@/context/UserContext';

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
    const currentStatus = status ?? { tier: 'free', userId } satisfies BillingStatus;
    const computed = {
      status,
      loading,
      userId,
      refresh,
      isFree: isFree(currentStatus),
      isPro: isPro(currentStatus),
      isElite: isElite(currentStatus),
      canUse: (feature: Feature) => engineCanUse(feature, currentStatus)
    } as BillingHelpers;

    return computed;
  }, [loading, refresh, status, userId]);
}
